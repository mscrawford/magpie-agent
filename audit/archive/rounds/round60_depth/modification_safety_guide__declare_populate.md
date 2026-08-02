# R60 depth audit — `cross_module/modification_safety_guide.md`

**Lens**: `declare_populate` (enter from the declaring/populating side: `declarations.gms`,
equation LHS, `.fx`/`.lo`/`.up` and parameter assignments; check the formulas the doc
attributes to each owner module's own equations).

**Ground truth**: pinned MAgPIE `develop` worktree at `2c02843ec`, clean
(`git status --porcelain` empty). All GAMS paths below are repo-relative inside that
worktree. All shell probes were run from the worktree root, each as its own standalone
command (no `find -exec … +` chaining, per the truncation hazard).

**Role-map cross-check**: `audit/integrated/depth_rolemap.json` was consulted FIRST for
every `vm_`/`pm_`/`im_`/`pcm_`/`fm_` attribution claim, then confirmed with a
both-endpoints grep. Two map-vs-code discrepancies were found and resolved in favour of
code (recorded in § *Map-vs-code discrepancies*).

- **Claims verified**: 41
- **Bugs**: 12 (0 Critical, 7 Major, 5 Minor)
- **Deferred**: 6

---

## Bugs

### B1 — Major — `attribution_populate` — doc:79

> `- NEVER modify `pcm_land` calculation (in modules/10_land/landmatrix_dec18/postsolve.gms:8-9)`

The citation itself is right (`postsolve.gms:9` is `pcm_land(j,land) = vm_land.l(j,land);`),
but the parenthetical localises the *whole* `pcm_land` calculation to one site. In current
develop **four modules write `pcm_land`, three of them outside Module 10**, all in default
realizations:

| write site | slice |
|---|---|
| `modules/10_land/landmatrix_dec18/start.gms:11` | all (`= pm_land_start`) |
| `modules/10_land/landmatrix_dec18/postsolve.gms:9` | all (`= vm_land.l`) |
| `modules/32_forestry/dynamic_may24/presolve.gms:101` | `"forestry"` |
| `modules/34_urban/exo_nov21/preloop.gms:17` | `"urban"` |
| `modules/35_natveg/pot_forest_may24/presolve.gms:39` | `"primforest"` (disturbance loss) |
| `modules/35_natveg/pot_forest_may24/presolve.gms:131` | `"secdforest"` |
| `modules/35_natveg/pot_forest_may24/presolve.gms:137` | `"other"` |

A reader auditing "the `pcm_land` calculation" from this guide would miss three modules
that overwrite slices *between* Module 10's postsolve and the next solve — exactly the
blast-radius asymmetry the doc's own Appendix A calls out (`gap ≥ +10` modules "whose
reach comes mostly from writing slices of variables they do not declare"). Tier is
borderline-Critical under the R20 anchor (wrong/incomplete populator set); held at Major
by the rubric tie-breaker because the doc gives a single-site pointer rather than an
enumerated "these are the only writers" list.

**Verify** (worktree root):
`rg -n 'pcm_land\([^)]*\)\s*=' modules/ --glob '*.gms'` → 9 hits; the 7 assignment sites
above (plus two `.fx` conditionals in `modules/71_disagg_lvst/foragebased_jul23/nl_fix.gms`
that read, not write, `pcm_land`).

**Fix**: replace with — "NEVER modify the `pcm_land` calculation. Module 10 declares it and
sets the whole array (`modules/10_land/landmatrix_dec18/start.gms:11`,
`postsolve.gms:9`), but Modules 32, 34 and 35 overwrite individual slices in
presolve/preloop (`modules/32_forestry/dynamic_may24/presolve.gms:101`,
`modules/34_urban/exo_nov21/preloop.gms:17`,
`modules/35_natveg/pot_forest_may24/presolve.gms:39,131,137`) — all four must be checked
together."

---

### B2 — Major — `attribution_populate` — doc:1097 (and 1094, 335, 353)

> `| \`vm_prod(j,k)\` | 8 | 17_production | vm_ | Cell-level production |`

Appendix B's **Producer** column attributes `vm_prod` to `17_production`. Module 17
**declares** `vm_prod(j,k)` (`modules/17_production/flexreg_apr16/declarations.gms:9`) but
never populates it — its only equation reads `vm_prod` on the RHS
(`modules/17_production/flexreg_apr16/equations.gms:11`). The populators are
`30_croparea` (`simple_apr24/equations.gms:15`, `kcr` — `simple_apr24` is the default,
`config/default.cfg:915`; same line in `detail_apr24`), `31_past`
(`endo_jun13/equations.gms:17`, `"pasture"`), `71_disagg_lvst`
(`foragebased_jul23/equations.gms:23,56`, `kli`) and `73_timber`
(`default/equations.gms:44,53`, `"wood"`/`"woodfuel"`). The doc's own §3.3 chain
(doc:353, `Module 30 (Croparea) → vm_prod(j,k) → Module 17`) states the correct direction
and contradicts Appendix B.

Same defect, weaker form, on doc:1094 / §1.2: `vm_land` is listed as a Module-10
"Critical Variable **Exported**" / Producer, but Module 10 only initialises the level
(`modules/10_land/landmatrix_dec18/start.gms:12`, `vm_land.l = pcm_land`) and constrains
totals; the slices are defined by `29_cropland` (`detail_apr24/equations.gms:12`,
`"crop"`), `32_forestry` (`dynamic_may24/equations.gms:56`, `"forestry"`), `34_urban`
(`exo_nov21/equations.gms:31`, `"urban"`), `35_natveg`
(`pot_forest_may24/equations.gms:11,13`, `"secdforest"`/`"other"`), with `31_past`
bounding `"past"` (`endo_jun13/presolve.gms:9`).

**Verify**: `rg -n 'vm_prod\(' modules/ --glob '*.gms'` (leading-LHS `=e=`/`=l=` sites are
30/31/71/73 only; module 17's single hit is on the RHS of `q17_prod_reg`);
`rg -n 'vm_land\(' modules/ --glob '*.gms' | grep -v '^modules/10_land'` and
`rg -n 'vm_land\.' modules/ --glob '*.gms' | grep -v '^modules/10_land'`.

**Fix**: rename the Appendix B column **Producer → Declared in**, and add a footnote:
"Declared-in is not populated-by. `vm_land` slices are populated by 29/31/32/34/35 and
`vm_prod` slices by 30/31/71/73; the declaring module owns the interface, not the
values." (Verifiers MANDATE: DECLARED / POPULATED / READ must be distinguished.)

---

### B3 — Major — `set_membership` — doc:367–377

> `**❌ MISTAKE 1**: Forgetting that \`vm_prod_reg\` only covers PLANT commodities`
> `* ERROR: Livestock modeled at regional level (Module 70), not cell level`
> `- **Module 17 handles**: Crops (kcr), pasture` / `- **Module 70 handles**: Livestock (kli) — regional only`

False. `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`
(`modules/17_production/flexreg_apr16/equations.gms:10-11`) ranges over set `k` (*Primary
products*), whose members include `livst_rum, livst_pig, livst_chick, livst_egg,
livst_milk, fish, wood, woodfuel`
(`modules/14_yields/managementcalib_aug19/sets.gms:12-18`; `yields` default is
`managementcalib_aug19`, `config/default.cfg:357`). Livestock production **is** a
cell-level variable: `vm_prod(j,kli)` is constrained by Module 71 in the default
realization `foragebased_jul23` (`config/default.cfg:2221`) at
`modules/71_disagg_lvst/foragebased_jul23/equations.gms:23` (`kli_rum` via the forage-feed
requirement) and `:56` (`kli_mon`, `q71_prod_mon_liv`). Timber likewise:
`modules/73_timber/default/equations.gms:44,53` populate `vm_prod(j2,"wood")` /
`vm_prod(j2,"woodfuel")`, which `q17_prod_reg` then aggregates like any other `k` member —
there is no "special aggregation" in Module 73.

The only genuine error in the doc's WRONG snippet is that `"beef"` is not a `kall` member
(the livestock meat product is `livst_rum`, `core/sets.gms:228-235`).

Note (honest provenance): the MAgPIE source comment at
`modules/17_production/flexreg_apr16/equations.gms:13` does say "plant commodity" — the
doc likely inherited that phrasing. The equation domain, not the comment, is the code
truth.

**Verify**: `sed -n '8,19p' modules/14_yields/managementcalib_aug19/sets.gms` (k members);
`rg -n 'vm_prod\(' modules/71_disagg_lvst modules/73_timber --glob '*.gms'`.

**Fix**: retitle the mistake to "Using a product label that is not a `kall` member", show
`vm_prod_reg(i,"livst_rum")`, and replace the FIX bullets with: "`q17_prod_reg` covers all
of set `k` — crops, pasture, **livestock, fish, wood and woodfuel**. Module 71
(`foragebased_jul23`, default) disaggregates livestock to clusters; Module 73 populates
the timber slices. `vm_prod_reg` slices *not* covered by `q17_prod_reg` are the residues
(`kres`, Module 18) and secondary products (`ksd`, Module 20) — see B4."

---

### B4 — Major — `attribution_populate` — doc:335 (and 353–360)

> `| \`vm_prod_reg(i,kall)\` | 8 modules | Regional production (for trade, demand) |`
> §3.3: `Module 30 (Croparea) → vm_prod(j,k) → Module 17 → vm_prod_reg(i,kall) → … Module 18 (Residues) → Module 20 (Processing) …`

`vm_prod_reg` is declared over `kall`
(`modules/17_production/flexreg_apr16/declarations.gms:10`) but `q17_prod_reg` only covers
`k`. `kres` (`res_cereals, res_fibrous, res_nonfibrous`) and `ksd`
(`oils, oilcakes, sugar, molasses, alcohol, ethanol, distillers_grain, brans, scp, fibres`)
are **not** in `k` (`modules/16_demand/sector_may15/sets.gms:10-14`;
`modules/14_yields/managementcalib_aug19/sets.gms:12-18`). Those slices are set elsewhere:

- `modules/18_residues/flexreg_apr16/equations.gms:78-81` — `q18_prod_res_reg(i2,kres) ..
  sum(cell(i2,j2), v18_prod_res(j2,kres)) =e= vm_prod_reg(i2,kres);` (18 = default,
  `config/default.cfg:625`)
- `modules/20_processing/substitution_may21/equations.gms:40-41` —
  `q20_processing_aggregation_cotton(i2) .. vm_prod_reg(i2,"cottn_pro") =e= …` (20 =
  default, `config/default.cfg:636`), plus the `ksd` balance at `:62`.

So Modules 18 and 20 are **not pure downstream consumers** of a variable Module 17
produces in full — they determine disjoint slices of it. The chain diagram is serial where
the code is partly parallel.

**Verify**: `rg -n 'vm_prod_reg' modules/18_residues modules/20_processing modules/21_trade --glob '*.gms'`
then read each hit's equation context (`sed -n '66,85p' modules/18_residues/flexreg_apr16/equations.gms`,
`sed -n '36,45p' modules/20_processing/substitution_may21/equations.gms`).

**Fix**: annotate the table row — "`vm_prod_reg(i,kall)`: Module 17 sets the `k` slice via
`q17_prod_reg`; the `kres` slice is set by Module 18 (`q18_prod_res_reg`) and the `ksd` /
`cottn_pro` slices by Module 20" — and split the §3.3 arrows for 18/20 out of the
downstream fan.

---

### B5 — Major — `data_flow_direction` — doc:496

> `   ├─ CDR Rewards → 32_forestry (afforestation incentive)`

`vm_reward_cdr_aff` is referenced in exactly three files:
`modules/56_ghg_policy/price_aug22/declarations.gms:43` (declare),
`…/equations.gms:68` (populate, `q56_reward_cdr_aff_reg`), `…/postsolve.gms`, and
`modules/11_costs/default/equations.gms:27` (read, `- vm_reward_cdr_aff(i2)`). **Module 32
never references it.** The real coupling runs the other way: Module 32 declares and
populates `vm_cdr_aff` (`modules/32_forestry/dynamic_may24/declarations.gms:83`), Module 56
*reads* it in `q56_reward_cdr_aff` (`modules/56_ghg_policy/price_aug22/equations.gms:77`),
and the resulting reward reaches forestry only through the shared objective via
`11_costs`. The sibling arrows in the same diagram mark economic knock-ons explicitly
(`[Economic knock-on: … via cost signal through 11_costs]`), so an unmarked top-level
arrow reads as a direct interface edge. This is the R51 / MANDATE-21 class.

**Verify**: `rg -n 'vm_reward_cdr_aff' modules/32_forestry --glob '*.gms'` → no match, with
positive control `rg -n 'vm_cdr_aff' modules/32_forestry --glob '*.gms'` → 5 hits;
`rg -ln 'vm_reward_cdr_aff' modules/ --glob '*.gms'` → 11_costs + 56 only.

**Fix**:
```
   ├─ vm_cdr_aff ← 32_forestry → vm_reward_cdr_aff → 11_costs (objective)
   │     └─ [Economic knock-on: afforestation incentive reaches 32 only via the objective]
```

---

### B6 — Major — `set_membership` — doc:482

> `| \`c56_emis_policy\` | reddnatveg_nosoil | 60+ policies | Which emissions priced |`

`scen56` has **44** members (`modules/56_ghg_policy/price_aug22/sets.gms:119-163`). The
doc's own cited source disagrees with it: `modules/module_56.md:38` says "44 policies".
(The adjacent `c56_pollutant_prices` "100+ IAM scenarios" **is** correct — `ghgscen56` has
102 members, `sets.gms:15-117`.)

**Verify**: python parse of the two set blocks in
`modules/56_ghg_policy/price_aug22/sets.gms` → `ghgscen56` 102 members (lines 15-117),
`scen56` 44 members (lines 119-163).

**Fix**: `60+ policies` → `44 policies (scen56, sets.gms:119-163)`.

---

### B7 — Major — `formula` — doc:827 (and 821)

> `2. Verify transition matrix: \`sum(land_from, vm_lu_transitions) = pcm_land\``

Inverted index. Code (`modules/10_land/landmatrix_dec18/equations.gms:19-25`):

```
q10_transition_to(j2,land_to)   .. sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e= vm_land(j2,land_to);
q10_transition_from(j2,land_from) .. sum(land_to,  vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);
```

Summing over `land_from` gives **`vm_land(j,land_to)`**, not `pcm_land`. The doc's own
§1.4 (doc:109-110) states both identities correctly, so §6.1 contradicts §1.4. The
adjacent doc:821 (`sum(vm_land) ≠ pcm_land`) also drops the outer sum on the RHS —
`q10_land_area` is `sum(land, vm_land) =e= sum(land, pcm_land)`
(`equations.gms:13-15`).

**Verify**: `sed -n '13,26p' modules/10_land/landmatrix_dec18/equations.gms`.

**Fix**: doc:827 → "Verify transition matrix: `sum(land_to, vm_lu_transitions(j,land_from,land_to)) = pcm_land(j,land_from)` (`q10_transition_from`) **and**
`sum(land_from, vm_lu_transitions(j,land_from,land_to)) = vm_land(j,land_to)`
(`q10_transition_to`)". doc:821 → `sum(land, vm_land) ≠ sum(land, pcm_land)`.

---

### B8 — Major — `attribution_read` — doc:177–181

> `**✅ SAFE**: Modifying transition costs (affects Module 29, 30, 32, 35)`
> `vm_cost_landcon.up(j,"primforest") = 1e6;  * USD/ha`

Two defects in one prescriptive block:

1. **Wrong module set.** `vm_cost_landcon(j,land)` is declared in `39_landconversion`
   (`modules/39_landconversion/calib/declarations.gms:13`; `calib` is the only realization
   and the default, `config/default.cfg:1288`) and referenced by exactly two
   modules: 39 (populate, `q39_cost_landcon`) and `11_costs` (read,
   `modules/11_costs/default/equations.gms:20`). Modules 29, 30, 32 and 35 never reference
   it. Also, in a Module-10 section, "transition costs" is Module 10's
   `vm_cost_land_transition` (`q10_cost`, `equations.gms:42-44`, 1 USD/ha on gross
   land-use change) — a different variable in a different module.
2. **Mechanism.** `vm_cost_landcon` is pinned by an equality
   (`q39_cost_landcon(j2,land) .. vm_cost_landcon(j2,land) =e= …`,
   `modules/39_landconversion/calib/equations.gms:12`). An upper bound on it cannot *raise*
   the conversion cost; it can only be slack or make the model infeasible. The lever for
   "higher cost for primforest conversion" is the module-39 cost parameters, not a `.up`.

**Verify**: `rg -n 'vm_cost_landcon' modules/29_cropland modules/30_croparea modules/32_forestry modules/35_natveg --glob '*.gms'`
→ no match, positive control `rg -c 'vm_land' modules/32_forestry --glob '*.gms'` → hits;
`rg -n 'vm_cost_landcon' modules/39_landconversion/*/declarations.gms modules/39_landconversion/*/equations.gms`.

**Fix**: retitle to "Modifying land-conversion cost **inputs** (Module 39; reaches the
objective via `11_costs` only)", drop the 29/30/32/35 list, and replace the `.up` snippet
with a parameter-level example, or move the whole pattern out of the Module 10 section and
point Module 10's "transition costs" at `vm_cost_land_transition` / `q10_cost`.

---

### B9 — Minor — `set_membership` — doc:174

> `vm_lu_transitions.fx(j,"forest","crop")$(pm_land_conservation(j,"forest") > 0) = 0;`

Presented as a ✅ SAFE pattern, but it will not compile:

- `"forest"` is not a member of `land` — `core/sets.gms:250-251` gives
  `/ crop, past, forestry, primforest, secdforest, urban, other /`. (The doc uses valid
  members elsewhere, e.g. doc:102 `"primforest"`.)
- `pm_land_conservation` is declared 4-dimensional —
  `pm_land_conservation(t,j,land,consv_type)`
  (`modules/22_land_conservation/area_based_apr22/declarations.gms:15`) — not `(j,land)`.
  Real usage: `pm_land_conservation(t,j,"primforest","protect")`
  (`modules/35_natveg/pot_forest_may24/presolve.gms:162`).

**Verify**: `rg -n -A12 '^ +land\b' core/sets.gms`;
`rg -n 'pm_land_conservation' modules/22_land_conservation/*/declarations.gms`.

**Fix**: `vm_lu_transitions.fx(j,"primforest","crop")$(sum(consv_type, pm_land_conservation(t,j,"primforest",consv_type)) > 0) = 0;`

---

### B10 — Minor — `other` (identifier dimensions) — doc:1095–1096

> `| \`im_pop_iso(t,iso)\` | 10 | 09_drivers | … |`
> `| \`pm_interest(t,i)\` | 9 | 12_interest_rate | … |`

Both are declared over `t_all`, not `t`: `im_pop_iso(t_all,iso)`
(`modules/09_drivers/aug17/declarations.gms:10`) and `pm_interest(t_all,i)`
(`modules/12_interest_rate/select_apr20/declarations.gms:9`, populated at
`preloop.gms:23`). `t` is the simulated-timestep subset of `t_all`; in an "Interface
Variable Reference" the distinction matters (`t_all` spans y1965-y2150).

**Verify**: `rg -n 'im_pop_iso' modules/09_drivers/*/declarations.gms`;
`rg -n 'pm_interest' modules/12_interest_rate/*/declarations.gms`.

**Fix**: `im_pop_iso(t_all,iso)`, `pm_interest(t_all,i)`.

---

### B11 — Minor — `data_flow_direction` — doc:629

> ```
> 10_land ←→ 35_natveg ←→ 22_land_conservation
> ```

Rendered as a two-hop bidirectional cycle. The cited source is explicit that the second
hop is one-way (`core_docs/Module_Dependencies.md:199-200`: "`22_land_conservation →
35_natveg (unidirectional: pm_land_conservation)`", "`10_land → 22_land_conservation
(unidirectional: vm_land)`"), and code agrees: Module 22 references only `fm_land_iso`,
`pcm_land`, `pm_land_conservation`, `vm_land`, `vm_treecover` — nothing declared or written
by Module 35 (35 declares `pm_max_forest_est`, `vm_land_other`, `vm_prod_natveg`,
`vm_cost_hvarea_natveg`, `vm_natforest_reduction`; none appear in 22).

**Verify**:
`rg -no '(vm_|pm_|im_|pcm_|fm_)[a-z_0-9]+' modules/22_land_conservation --glob '*.gms' | awk -F: '{print $3}' | sort -u`
→ the five names above;
`rg -n '^\s*(vm_|pm_|im_|pcm_)[a-z_0-9]+\s*\(' modules/35_natveg/pot_forest_may24/declarations.gms`.

**Fix**: reproduce the source's three-line form (bidirectional 10↔35; unidirectional
22→35 and 10→22) so the test protocol does not send a reader looking for a feedback that
does not exist.

---

### B12 — Minor — `citation` — doc:609, doc:1103, doc:507

Three range citations point at materially different sections of the docs they name
(section *names* are correct, so each is recoverable — hence Minor, not Major):

| doc line | claim | actual location |
|---|---|---|
| 609 | "Critical Feedback Cycles (from Module_Dependencies.md:151-179)" | §4.1 *Critical Feedback Cycles* is at `core_docs/Module_Dependencies.md:184-217`; 151-179 is §3.1 Architectural Layers + §3.2 Hub-and-Spoke |
| 1103 | "Module_Dependencies.md §2.1 (lines 46-59)" | §2.1 *Most Connected Variables* is at `core_docs/Module_Dependencies.md:80-97`; 46-59 is §1.2 prose (Owns/Reaches/gap definitions) |
| 507 | "carbon_balance_conservation.md:450-550 for full carbon-policy interactions" | 450-550 is §6 Chapman-Richards forest growth + §7.1/§7.2 (Modules 52, 59). GHG-policy interaction content is §7.4 (`:587`) and §8.2 (`:662`) |

**Verify**: `grep -n '^#\{1,4\} ' core_docs/Module_Dependencies.md`;
`grep -n '^#\{2,4\} ' cross_module/carbon_balance_conservation.md`.

**Fix**: cite by section anchor (`§4.1`, `§2.1`, `§7.4 / §8.2`) rather than line range, or
refresh the ranges to `184-217`, `80-97`, `587-606 / 662-694`.

---

## Verified correct (no bug)

These were the highest-risk claims under this lens and they all held up — recording them
so a later round does not re-litigate:

1. **Module 10 consumer counts (doc:46-50) are all correct**, including the near-miss:
   `vm_land` 10, `vm_landexpansion` 4, `vm_landreduction` 2, `pcm_land` 12,
   `vm_lu_transitions` 3. A naive `rg -l 'vm_land[.(]'` returns only 9 / 3 / 1 and looks
   like the doc over-counts by one on three rows. It does not: **`58_peatland` passes the
   bare names as macro arguments** — `m58_LandMerge(vm_land,vm_land_forestry,"j2")` at
   `modules/58_peatland/v2/equations.gms:23`, and the same form for `vm_landexpansion` at
   `:28` and `vm_landreduction` at `:31` — invisible to any `NAME(` / `NAME.` pattern.
   Confirmed with `rg -n 'vm_land' modules/58_peatland --glob '*.gms'` plus a positive
   control. **This is a live false-positive trap for future greps in this repo.**
2. doc:54-58 — the 10-module direct-`vm_land` list and the 18-module union
   (11,13,14,22,29,30,31,32,34,35,39,44,50,56,58,59,71,80) both reproduce exactly from the
   role map union over `vm_land`, `vm_landexpansion`, `vm_landreduction`,
   `vm_lu_transitions`, `vm_landdiff`, `pcm_land`, `pm_land_hist`, `pm_land_start`,
   `vm_cost_land_transition`.
3. doc:157 — "ALL 11 modules" (10 `vm_land` consumers + `39_landconversion`) reproduces.
4. doc:109-110 — the transition-matrix row/column identities match
   `q10_transition_from` / `q10_transition_to` exactly.
5. doc:38, 202, 327, 454 — realizations `landmatrix_dec18`, `default`, `flexreg_apr16`,
   `price_aug22` are the real directory names **and** the config defaults
   (`config/default.cfg:232, 236, 615, 1634`).
6. doc:40 — "7 land types" matches `core/sets.gms:250-251`.
7. doc:217 — "Module 11 depends on cost variables from **27** modules": the 32 `vm_*`
   terms in `q11_cost_reg` resolve to exactly 27 distinct declaring modules
   (10,13,18,20,21,29,30,31,32,34,35,38,39,40,41,42,44,50,54,56,57,58,59,60,70,71,73).
8. doc:219-227 — every cost-variable → source-module attribution in the §2.2 table is
   right (incl. all three `vm_cost_trade_*` from 21_trade).
9. doc:229 — "module_11.md (lines 84-115)" lands on the `q11_cost_reg` block. Valid.
10. doc:245-247, 275 — the `q11_cost_reg` / `v11_cost_reg` names and the
    `- vm_reward_cdr_aff(i2)` sign convention match
    `modules/11_costs/default/equations.gms:15,27`.
11. doc:389-392 — `pm_prod_init` initialization cited at
    `modules/17_production/flexreg_apr16/presolve.gms:10` is an **exact** match, formula
    included.
12. doc:336 — `pm_prod_init` "1 module" (`38_factor_costs`) is correct.
13. doc:462-464 — `vm_emission_costs` consumers (`11_costs`, `15_food`) verified:
    `modules/15_food/anthro_iso_jun22/intersolve.gms:23` reads `vm_emission_costs.l` for
    `p15_tax_recycling` (15 default = `anthro_iso_jun22`, `config/default.cfg:413`) — a
    solution-level read a `vm_emission_costs(` grep would miss.
    `im_pollutant_prices(t_all,i,pollutants,emis_source)` dims are exact, and the
    `modules/57_maccs/on_aug22/preloop.gms:24-25` citation is exact.
14. doc:466, 546 — `q56_emission_costs` and the `q56_emis_pricing_co2` mechanism
    (`pcm_carbon_stock … - vm_carbon_stock …`) match
    `modules/56_ghg_policy/price_aug22/equations.gms:56-58, 19-22`.
15. doc:481-484 — `c56_pollutant_prices` = `R34M410-SSP2-NPi2025`, `c56_emis_policy` =
    `reddnatveg_nosoil`, `c56_carbon_stock_pricing` = `actualNoAcEst`,
    `s56_c_price_induced_aff` = 1 all verified in BOTH
    `modules/56_ghg_policy/price_aug22/input.gms:84,86,90,69` and `config/default.cfg`.
    The doc:535 pointer to `input.gms:69` is exact.
16. doc:1094-1099 — Appendix B consumer counts (10/10/9/8/8/8) all reproduce under the
    footnote's own method (word-boundary form; the bare `grep -l 'vm_prod'` in the
    footnote would over-count by matching `vm_prod_reg`).
17. doc:1060-1070 — Appendix A reproduces `core_docs/Module_Dependencies.md:29-41` row for
    row.

---

## Map-vs-code discrepancies (code wins; noted for the map's maintainers)

- `depth_rolemap.json` lists `21_trade` under `vm_prod_reg.populated_by`. Every Module 21
  occurrence is inside a `sum(supreg(h2,i2), …)` on an inequality LHS
  (`modules/21_trade/selfsuff_reduced/equations.gms:13,19,32,40,65,72`) — a **read**, not a
  populate. Same for `29_cropland` under `vm_lu_transitions.populated_by`
  (`modules/29_cropland/detail_apr24/equations.gms:60` is `sum(land_snv, …) =g= …`). No doc
  claim depends on either, so no bug was filed — but do not use the map's `populated_by`
  as a leaf without the LHS check.
- `pm_interest.populated_by` is empty in the map although
  `modules/12_interest_rate/select_apr20/preloop.gms:23` assigns it (multi-line RHS).
  Again: read-side heuristic limit, not a doc bug.

---

## Deferred (not verified — no bug filed)

1. §2.2 "Typical Magnitude (USD17/yr)" cost ranges (doc:221-227) — need a solved GDX; not
   derivable from source.
2. §5.2 / §5.3 R snippets — `magpie4` function existence/signatures (`nr_inputs`,
   `nr_outputs`, `nr_soil_change`, `water_avail`, `land_transitions`, `land_conservation`,
   `trade_balance`) not checked against the renv-pinned magpie4 clone this session.
3. Appendix A `Owns / Reaches / gap / Depends On` numbers — reproduce the source doc
   verbatim, but `audit/tools/compute_module_centrality.py` was not re-run against develop
   `2c02843ec`, so the *underlying* figures are inherited, not re-measured.
4. Risk-tier labels (🔴 EXTREME / 🟠 HIGH / 🟡 MEDIUM in §1.2, §3.2) — judgment calls, not
   code-checkable.
5. doc:47 describes `vm_lu_transitions` as "gross between-type transitions"; the matrix
   also carries the same-type diagonal (`q10_landexpansion` excludes it explicitly with
   `$(not sameas(land_from,land_to))`). Arguably intended shorthand — flagged only here.
6. doc:514, 529 use `im_pollutant_prices(t,i,"co2_c","all")` in ❌-labelled snippets;
   whether `"all"` is a valid `emis_source` member was not checked (the snippets are
   deliberately-wrong examples about price magnitude, so the label is incidental).
