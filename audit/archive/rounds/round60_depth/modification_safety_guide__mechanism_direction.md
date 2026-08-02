# R60 depth audit — `cross_module/modification_safety_guide.md`

**Lens**: `mechanism_direction` (equation bodies, cross-module data-flow direction, serial-vs-parallel hand-offs, set-membership/count claims)
**Ground truth**: MAgPIE `develop` read-only worktree (HEAD `2c02843ec`, "Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Role map**: `audit/integrated/depth_rolemap.json` (checked first for every DECLARED/POPULATED/READ claim, then confirmed with both-endpoint greps)
**Claims verified**: 61 · **Bugs**: 13 (1 Critical, 11 Major, 1 Minor) · all `confirmed: true`

---

## What checked out clean (so the bug list is read in proportion)

These are the load-bearing claims I verified and could NOT break — worth recording so a
future round does not re-litigate them:

| Doc claim | Verdict |
|---|---|
| Realizations `10_land/landmatrix_dec18`, `11_costs/default`, `17_production/flexreg_apr16`, `56_ghg_policy/price_aug22` are the defaults | ✅ `config/default.cfg:232,236,615,1634` |
| §1.2 consumer counts: `vm_land` 10, `vm_lu_transitions` 3, `vm_landexpansion` 4, `vm_landreduction` 2, `pcm_land` 12 | ✅ all five reproduce exactly |
| §1.2 the named 10 `vm_land` consumers (22,29,30,31,32,34,35,50,58,59) | ✅ — note M58 is reachable only through the macro form `m58_LandMerge(vm_land,…)` (`modules/58_peatland/v2/equations.gms:23`), invisible to a `vm_land(` grep. The doc is right and a naive grep is wrong. |
| §1.2 the 18-module union touched by any M10 interface variable | ✅ exact set match |
| §1.5 "ALL 11 modules" touched by the four transition variables | ✅ exact |
| §1.4 row/column sum identities (`sum(land_to,…)=pcm_land`, `sum(land_from,…)=vm_land`) | ✅ matches `q10_transition_from`/`q10_transition_to` |
| §2.2 all seven cost-variable → source-module attributions | ✅ role map + `q11_cost_reg` |
| §2.2 "Module 11 depends on cost variables from 27 modules" | ✅ exactly 27 distinct declaring modules across 32 `vm_` terms |
| §2.2 unit `mio. USD17MER/yr`; §2.3 `q11_cost_reg`/`v11_cost_reg`; `- vm_reward_cdr_aff(i2)` sign | ✅ `modules/11_costs/default/{declarations,equations}.gms` |
| §3.2 `vm_prod_reg` 8 consumers (16,18,20,21,38,50,70,71); `pm_prod_init` → 38 only | ✅ |
| §3.4 `pm_prod_init` formula + citation `presolve.gms:10` | ✅ character-exact |
| §4.2 `vm_emission_costs` → {11,15}, incl. the M15 `intersolve.gms` food-tax recycling read | ✅ `modules/15_food/anthro_iso_jun22/intersolve.gms:23` |
| §4.2 `im_pollutant_prices` → 57 only, with `preloop.gms:24-25` | ✅ character-exact |
| §4.3 defaults: `R34M410-SSP2-NPi2025`, `reddnatveg_nosoil`, `actualNoAcEst`, `s56_c_price_induced_aff=1`; "100+" price scenarios (=102) | ✅ (the one exception is the `c56_emis_policy` option count — B10) |
| §4.5 `q56_emis_pricing_co2` uses `(pcm_carbon_stock − vm_carbon_stock)` | ✅ (the *inference drawn from it* is B2) |
| Appendix A: every Owns/Reaches/gap/DependsOn cell, the band rule, the ⚠ marks, the `11_costs` footnote | ✅ re-ran `audit/tools/compute_module_centrality.py --table`; 11/11 rows identical |
| Appendix B: all six consumer counts and producer attributions | ✅ |

---

## Bugs

### B1 — Critical — `mechanism` — doc:367 (§3.4 MISTAKE 1)

> "**❌ MISTAKE 1**: Forgetting that `vm_prod_reg` only covers PLANT commodities … `* ERROR: Livestock modeled at regional level (Module 70), not cell level`" (367, 371)
> "- **Module 17 handles**: Crops (kcr), pasture / - **Module 70 handles**: Livestock (kli) — regional only / - **Module 73 handles**: Timber — special aggregation" (375-377)

**Reality.** `q17_prod_reg` is declared over the full primary-product set `k`, not over
`kcr`+pasture:

```gams
q17_prod_reg(i2,k) ..
vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
```
`modules/17_production/flexreg_apr16/equations.gms:10-11`

`k` has 28 members and explicitly contains `livst_rum, livst_pig, livst_chick, livst_egg,
livst_milk, fish, wood, woodfuel`
(`modules/14_yields/managementcalib_aug19/sets.gms:12-17`; that realization is the default,
`config/default.cfg:357`). So the snippet the doc labels an ERROR — regional livestock
production as the cell sum of `vm_prod` — is *exactly what the code does*.

Livestock **is** a cell-level quantity: `71_disagg_lvst` (default `foragebased_jul23`,
`config/default.cfg:2221`) writes/constrains `vm_prod(j2,kli_rum)` and `vm_prod(j2,kli_mon)`
(`modules/71_disagg_lvst/foragebased_jul23/equations.gms:23,56`; the `foragebased_aug18`
variant defines it outright in `q71_sum_rum_liv`, `…/foragebased_aug18/equations.gms:37-38`).
M70 does not *produce* regional livestock output — it **reads** `vm_prod_reg(i2,kap)` /
`vm_prod_reg(i2,kli)` to derive feed demand and factor costs
(`modules/70_livestock/fbask_jan16/equations.gms:18,60`). Timber is not "special
aggregation" either: `73_timber` writes `vm_prod(j2,"wood")` / `vm_prod(j2,"woodfuel")`
(`modules/73_timber/default/equations.gms:44,53`) and those two members are in `k`, so they
go through the same `q17_prod_reg`.

**Why Critical.** This is the *modification* guide for M17. A developer who narrows the
equation domain to `kcr` on this advice silently deletes regional production for five
livestock products, fish, wood and woodfuel — breaking feed balance (M70), trade (M21) and
timber costs (M73). Rubric trigger: "make a load-bearing modification that breaks the model".

**Verify.**
```
$ sed -n 10,11p /tmp/magpie_develop_ro/modules/17_production/flexreg_apr16/equations.gms
q17_prod_reg(i2,k) ..
vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
$ sed -n 12,17p /tmp/magpie_develop_ro/modules/14_yields/managementcalib_aug19/sets.gms
  k(kall) Primary products
       / … livst_rum, livst_pig, livst_chick, livst_egg, livst_milk, fish, wood, woodfuel/
$ rg -n "vm_prod\(j2,kli" /tmp/magpie_develop_ro/modules/71_disagg_lvst/foragebased_jul23/equations.gms
23:… vm_prod(j2,kli_rum) …
56:                 vm_prod(j2,kli_mon) =l=
```

**Fix.** Replace MISTAKE 1 with: `q17_prod_reg` aggregates **all** of `k` — crops, pasture,
the five `kli` products, fish, wood and woodfuel. Cell-level `vm_prod` slices are written by
`30_croparea` (`kcr`), `31_past` (pasture), `71_disagg_lvst` (`kli`) and `73_timber`
(wood/woodfuel); M70 and M21 are *consumers* of `vm_prod_reg`. The real hazard to warn about
is the reverse of what is written: narrowing the `k` domain of `q17_prod_reg` drops whole
commodity classes. Also replace the non-member label `"beef"` with `"livst_rum"`.

---

### B2 — Major — `mechanism` — doc:550 (§4.5 MISTAKE 3)

> "**Implication**: Emission costs lag land-use change by one timestep" (550)
> "- Don't expect instant response to price changes" (555)

**Reality.** The doc's premise is right (`q56_emis_pricing_co2` uses
`pcm_carbon_stock − vm_carbon_stock`, `modules/56_ghg_policy/price_aug22/equations.gms:19-22`)
but the conclusion inverts the mechanism. `pcm_carbon_stock` is the *fixed baseline* from the
previous solve; `vm_carbon_stock` is a **decision variable of the current solve**, tied to
current land through `q35_carbon_primforest/secdforest/other`
(`modules/35_natveg/pot_forest_may24/equations.gms:42-55`, arguments `vm_land`,
`v35_secdforest`, `vm_land_other`). Deforesting in period *t* therefore raises the priced
emission in period *t*'s own objective. There is no one-period lag in the response; the
difference is a within-step flux, not a lagged signal. (The doc's own line 553, "Emission
costs in 2040 reflect 2030-2040 land change", is the correct reading and contradicts 550/555.)

The one genuine delay in the default config is unrelated and unmentioned:
`c56_mute_ghgprices_until <- "y2030"` (`config/default.cfg:1747`).

**Verify.**
```
$ sed -n 19,22p /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/equations.gms
 q56_emis_pricing_co2(i2,emis_oneoff) ..
  v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
                 sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
                 (pcm_carbon_stock(…,"actual") - vm_carbon_stock(…,"%c56_carbon_stock_pricing%"))/m_timestep_length);
$ rg -n "vm_carbon_stock\(j2" /tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/equations.gms
43: vm_carbon_stock(j2,"primforest",ag_pools,stockType) =e=   [m_carbon_stock(vm_land,…)]
```

**Fix.** Recast MISTAKE 3 as "the priced quantity is a *stock difference against a fixed
previous-period baseline*, so it prices the whole `m_timestep_length` interval at once and is
scaled by `1/m_timestep_length`" — and delete "lag … by one timestep" / "Don't expect instant
response". If a delay caveat is wanted, cite `c56_mute_ghgprices_until` (`y2030` by default).

---

### B3 — Major — `formula` — doc:827 (§6.1 Error Pattern 1, Fix step 2)

> "2. Verify transition matrix: `sum(land_from, vm_lu_transitions) = pcm_land`"

**Reality.** Inverted. `sum(land_from, …)` equals `vm_land`, not `pcm_land`:

```gams
q10_transition_to(j2,land_to)   .. sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e= vm_land(j2,land_to);
q10_transition_from(j2,land_from) .. sum(land_to,   vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);
```
`modules/10_land/landmatrix_dec18/equations.gms:19-25`

The same document states it correctly at lines 109-110, so this is a local contradiction, not
an inherited one. A developer debugging an infeasibility with the wrong invariant gets a false
alarm on every cell where land use changed.

**Verify.** `sed -n 19,25p /tmp/magpie_develop_ro/modules/10_land/landmatrix_dec18/equations.gms` → as quoted.

**Fix.** `sum(land_to, vm_lu_transitions(j,land_from,land_to)) = pcm_land(j,land_from)` **and**
`sum(land_from, vm_lu_transitions(j,land_from,land_to)) = vm_land(j,land_to)` (`q10_transition_from`
/ `q10_transition_to`).

---

### B4 — Major — `formula` — doc:148 (§1.5 Testing Protocol, test 2)

> "# Verify row sums = column sums … `stopifnot(all(abs(row_sums - col_sums) < 1e-6))`"
> with `row_sums <- dimSums(transitions, dim="to")`, `col_sums <- dimSums(transitions, dim="from")`

**Reality.** The asserted invariant is false whenever land use changes. Per
`q10_transition_from`/`q10_transition_to`, summing over `to` yields `pcm_land(j,land_from)` and
summing over `from` yields `vm_land(j,land_to)`; element-wise equality of the two would require
`vm_land = pcm_land` for every pool — i.e. a completely static land system. Only the **grand
totals** are equal, and that is the separate constraint
`q10_land_area(j2) .. sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))`
(`modules/10_land/landmatrix_dec18/equations.gms:13-15`). Labelled a test that "MUST pass",
this one fails on any scenario with land-use change.

**Verify.** `sed -n 13,25p /tmp/magpie_develop_ro/modules/10_land/landmatrix_dec18/equations.gms` → the
three equations above.

**Fix.** Test the two real identities separately (`dimSums(transitions,dim="to")` vs `pcm_land`;
`dimSums(transitions,dim="from")` vs `land(gdx)`), or, if only one check is wanted, compare the
scalar totals `sum(row_sums)` vs `sum(col_sums)` (the `q10_land_area` invariant).

---

### B5 — Major — `data_flow_direction` — doc:629 (§5.1 cycle 2)

> "```\n   10_land ←→ 35_natveg ←→ 22_land_conservation\n```"

**Reality.** `10_land ←→ 35_natveg` is genuinely bidirectional (M35 reads/writes `vm_land`,
`pcm_land`, `vm_landexpansion`, `vm_lu_transitions`; M10 reads M35's `vm_landdiff_natveg` in
`q10_landdiff`, `modules/10_land/landmatrix_dec18/equations.gms:50-54`). The second arrow is
**not** bidirectional: `22_land_conservation` declares and initialises `pm_land_conservation`
(`modules/22_land_conservation/area_based_apr22/presolve_ini.gms:54`), M35 reads it and even
overwrites slices of it (`modules/35_natveg/pot_forest_may24/presolve.gms:149,197,198`), but
**no variable declared by M35 is read by M22** — the readers of the overwritten parameter are
M29 and M35 itself. The upstream source has already been corrected to say exactly this
("`22_land_conservation → 35_natveg (unidirectional: pm_land_conservation)`",
`core_docs/Module_Dependencies.md:196-203`); this guide still carries the pre-correction form.

**Verify.**
```
$ python3 -c "import json;m=json.load(open('audit/integrated/depth_rolemap.json'));\
print([v for v,d in m.items() if (d['declared_in'] or '')[:2]=='35' and '22' in set(d['read_by'])|set(d['populated_by'])])"
[]
$ rg -n "pm_land_conservation" /tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/presolve.gms | head -3
149: pm_land_conservation(t,j,land_natveg,"protect")$(…) = pcm_land(j,land_natveg);
```
(positive control: the same probe with `('22','35')` returns `pm_land_conservation`.)

**Fix.** Mirror the corrected upstream form: `10_land ←→ 35_natveg` (true bidirectional) on one
line, `22_land_conservation → 35_natveg (unidirectional: pm_land_conservation)` on the next, and
add the non-obvious back-edge that *does* exist — M35 rewrites slices of `pm_land_conservation`
that **M29** subsequently reads (`modules/29_cropland/simple_apr24/equations.gms:41`).

---

### B6 — Major — `data_flow_direction` — doc:645 (§5.1 cycle 3)

> "3. **Forest-Carbon Cycle** (5-module feedback):
> ```\n   32_forestry ←→ 30_croparea ←→ 10_land ←→ 35_natveg ←→ 56_ghg_policy\n```"

**Reality.** Three of the four arrows are one-way and the chain never closes:

| claimed | code |
|---|---|
| `32 ←→ 30` | one-way `30 → 32`: M32 reads `vm_area` (declared in `30_croparea`); M30 reads nothing M32 declares |
| `30 ←→ 10` | one-way `10 → 30`: M30 reads `vm_land`, `fm_luh2_side_layers`; M10 reads nothing M30 declares |
| `10 ←→ 35` | ✅ genuinely bidirectional |
| `35 ←→ 56` | one-way `35 → 56`: M35 *populates* `vm_carbon_stock` (declared in M56, `modules/35_natveg/pot_forest_may24/equations.gms:42-55`), which M56 reads in `q56_emis_pricing_co2`. M35 reads nothing M56 declares |

And there is **no** return edge from M56 into 10/29/30/32/35 at all — `rg -n
"im_pollutant_prices|vm_emission_costs|vm_reward_cdr_aff|pcm_carbon_stock|s56_|p56_"` over
`modules/10_land/`, `modules/30_croparea/`, `modules/35_natveg/`, `modules/32_forestry/`
returns only prose comments. The loop closes **only** through the shared objective:
`vm_emission_costs` and `vm_reward_cdr_aff` enter `q11_cost_reg`
(`modules/11_costs/default/equations.gms:26-27`), which `80_optimization` minimises. That is a
price feedback through the objective, not a 5-module data cycle — the same
parallel-not-serial distinction as the R51 finding.

**Verify.**
```
$ rg -n "im_pollutant_prices|vm_emission_costs|vm_reward_cdr_aff|pcm_carbon_stock" \
    /tmp/magpie_develop_ro/modules/10_land/ /tmp/magpie_develop_ro/modules/30_croparea/ /tmp/magpie_develop_ro/modules/35_natveg/
(no output)
$ rg -c "vm_land" /tmp/magpie_develop_ro/modules/30_croparea/simple_apr24/equations.gms
1                     # positive control: the directory is searchable
```

**Fix.** Redraw as the directed chain it is —
`10_land → 30_croparea → 32_forestry`, `10_land ←→ 35_natveg`, `35_natveg → 56_ghg_policy (writes vm_carbon_stock)` —
and state explicitly that the feedback to land allocation returns via `11_costs`/`80_optimization`
(objective), not via any M56 interface variable.

---

### B7 — Major — `data_flow_direction` — doc:496 (§4.4 interaction diagram)

> "   ├─ CDR Rewards → 32_forestry (afforestation incentive)"

**Reality.** Direction inverted. `vm_reward_cdr_aff(i)` is declared and populated in M56
(`modules/56_ghg_policy/price_aug22/declarations.gms:43`, `…/equations.gms:67-71`) and is read
by exactly one other module: `11_costs` (`modules/11_costs/default/equations.gms:27`,
`- vm_reward_cdr_aff(i2)`). The variable that crosses the 56↔32 boundary travels the other
way: `vm_cdr_aff` is declared and populated in `32_forestry`
(`modules/32_forestry/dynamic_may24/declarations.gms:83`, `…/equations.gms:37,42`) and **read
by M56** in `q56_reward_cdr_aff` (`modules/56_ghg_policy/price_aug22/equations.gms:77`).
Nothing declared by M56 is referenced anywhere in `modules/32_forestry/` — the incentive
reaches forestry only through the objective function. The sibling arrows in the same diagram
are code-anchored data flows (one even carries a `file:line`), so this one reads as a data flow
too.

**Verify.**
```
$ rg -n "s56_|p56_|im_pollutant_prices|vm_reward_cdr_aff" /tmp/magpie_develop_ro/modules/32_forestry/
…/realization.gms:16:*' [56_ghg_policy] module. …        (comment only)
…/equations.gms:34:*' … to the [56_ghg_policy] module.   (comment only)
…/module.gms:18:*' … to the GHG policy module …          (comment only)
$ rg -n "vm_cdr_aff" /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/equations.gms
77:               (sum(aff_effect,(1-s56_buffer_aff)*vm_cdr_aff(j2,ac,aff_effect)) * …
```

**Fix.** `CDR Rewards → 11_costs (objective; `- vm_reward_cdr_aff`) → afforestation incentive
realised in 32_forestry`, with the note that the only interface variable crossing 56↔32 is
`vm_cdr_aff`, flowing **32 → 56**.

---

### B8 — Major — `set_membership` — doc:174 (§1.6 "SAFE" pattern 1)

> "```gams\nvm_lu_transitions.fx(j,\"forest\",\"crop\")$(pm_land_conservation(j,\"forest\") > 0) = 0;\n```"

**Reality.** Two domain errors in a pattern the guide marks ✅ SAFE and invites the reader to
copy:
1. `"forest"` is not a member of `land` — the set is `/ crop, past, forestry, primforest,
   secdforest, urban, other /` (`core/sets.gms:250-251`), and `land_from`/`land_to` are aliases
   over it.
2. `pm_land_conservation` is four-dimensional `(t,j,land,consv_type)`
   (`modules/22_land_conservation/area_based_apr22/presolve_ini.gms:54`;
   used as `pm_land_conservation(ct,j2,land_snv,consv_type)` in
   `modules/29_cropland/simple_apr24/equations.gms:41`), not `(j,land)`.

As written the snippet raises GAMS domain errors ($170/$171) rather than doing anything.
(`vm_land.fx(j,"forest")` at doc:121 has the same non-member label, though it sits inside a
block already labelled WRONG.)

**Verify.**
```
$ sed -n 249,252p /tmp/magpie_develop_ro/core/sets.gms
  land Land pools
        / crop, past, forestry, primforest, secdforest, urban, other /
$ rg -n "pm_land_conservation\(t,j,land," /tmp/magpie_develop_ro/modules/22_land_conservation/area_based_apr22/presolve_ini.gms | head -1
54:pm_land_conservation(t,j,land,"protect") = p22_conservation_area(t,j,land);
```

**Fix.** Use a real pool and the full domain, e.g.
`vm_lu_transitions.fx(j,"primforest","crop")$(sum(ct, pm_land_conservation(ct,j,"primforest","protect")) > 0) = 0;`
and fix the `"forest"` label at doc:121 to `"primforest"`/`"secdforest"`.

---

### B9 — Major — `mechanism` — doc:177 (§1.6 "SAFE" pattern 2)

> "**✅ SAFE**: Modifying transition costs (affects Module 29, 30, 32, 35)" (177)
> "`vm_cost_landcon.up(j,\"primforest\") = 1e6;  * USD/ha`" (180), captioned "Higher cost for primary forest conversion"

**Reality.** Three separate errors:
1. **The mechanism does the opposite of the caption.** `vm_cost_landcon` is *determined* by an
   equality, `q39_cost_landcon(j2,land) .. vm_cost_landcon(j2,land) =e= …`
   (`modules/39_landconversion/calib/equations.gms:12`). An upper bound on a cost the solver
   already minimises cannot raise it — it is either slack (no effect) or binding, in which case
   it makes the model **infeasible**. To raise conversion costs you change the cost parameters
   feeding `q39_cost_landcon`.
2. **Wrong unit.** `vm_cost_landcon(j,land)` is declared `mio. USD17MER per yr`
   (`modules/39_landconversion/calib/declarations.gms:13`), not USD/ha — the doc's own §2.3
   MISTAKE 2 flags this exact confusion as an error while §1.6 commits it under a ✅ SAFE label.
3. **Wrong affected set.** `vm_cost_landcon` is read by `11_costs` only
   (`modules/11_costs/default/equations.gms:20`; role map `read_by: ['11','39']`). Modules 29,
   30, 32, 35 never reference it; they respond, if at all, through the objective.

**Verify.**
```
$ rg -n "vm_cost_landcon" /tmp/magpie_develop_ro/modules/39_landconversion/calib/{declarations,equations}.gms
declarations.gms:13: vm_cost_landcon(j,land)  Costs for land expansion and reduction (mio. USD17MER per yr)
equations.gms:12:q39_cost_landcon(j2,land) .. vm_cost_landcon(j2,land) =e=
$ rg -ln "vm_cost_landcon" /tmp/magpie_develop_ro/modules/ | awk -F/ '{print $5}' | sort -u
11_costs
39_landconversion
```

**Fix.** Replace the example with a parameter-side change inside `39_landconversion` (the
inputs to `q39_cost_landcon`), state the unit as `mio. USD17MER per yr`, and correct the
affected-module note to "`11_costs` is the only reader; 29/30/32/35 respond through the
objective, not through this variable".

---

### B10 — Major — `set_membership` — doc:482 (§4.3 policy-lever table)

> "| `c56_emis_policy` | reddnatveg_nosoil | **60+ policies** | Which emissions priced |"

**Reality.** The closed set `scen56` has exactly **44** members
(`modules/56_ghg_policy/price_aug22/sets.gms:119-163`, one member per line, `none` … 
`co2_reddnatveg_nosoil_peatland`). The doc's own cited source says 44
(`modules/module_56.md:37`, and doc:486 points at that very table, "module_56.md lines 32-42").
The sibling claim in the same table, "100+ IAM scenarios" for `c56_pollutant_prices`, is
correct — `ghgscen56` has 102 members (`…/sets.gms:15-117`).

**Verify.**
```
$ awk 'NR>=120 && NR<=163' /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/sets.gms | wc -l
      44
```
(members run one-per-line from `/ none,` at 120 to `co2_reddnatveg_nosoil_peatland /` at 163.)

**Fix.** `44 policies` (and, if a moving count is unwanted, cite the set location instead of a
number: "`scen56` in `modules/56_ghg_policy/price_aug22/sets.gms:119-163`").

---

### B11 — Major — `citation` — doc:609 (§5.1 header)

> "**Critical Feedback Cycles** (from Module_Dependencies.md:151-179):"

**Reality.** `core_docs/Module_Dependencies.md:151-179` is §3.1's architectural-layer diagram
(Layers 4-6) plus §3.2 "Hub-and-Spoke Patterns" — materially different content. The circular
dependencies live in §4.1, lines 182-216, and the three cycles this section reproduces are at
188-190, 196-203 and 212-216. The stale pointer is also what hides B5: the corrected cycle-2
text sits at 196-203, thirty lines past the cited range.

**Verify.** `awk 'NR>=151 && NR<=179' core_docs/Module_Dependencies.md` → layer diagram + hub
counts; `grep -n "#### 4.1 Critical Feedback Cycles" core_docs/Module_Dependencies.md` → `184`.

**Fix.** Cite by section: "(from `core_docs/Module_Dependencies.md` §4.1 Critical Feedback
Cycles)" — the convention Appendix A of this same file already adopted after an identical drift.

---

### B12 — Major — `other` (centrality / risk-tier claim) — doc:450 (§4.1), scope claim at doc:11

> "**Centrality**: HIGH" (450, Module 56)
> "This guide covers the **4 highest-centrality modules** in MAgPIE" (11)

**Reality.** The document defines its own band rule in Appendix A: "🔴 CRITICAL at `Reaches`
≥ 18, 🟠 HIGH at ≥ 12, 🟡 MEDIUM below" (doc:1072-1073). Re-running the generator the appendix
cites, `56_ghg_policy` has **Owns 5, Reaches 5, DependsOn 13** — rank 22 of 46 by `Reaches`,
i.e. MEDIUM under the doc's own rule, not HIGH. Nor are these the four highest-centrality
modules by either surviving metric: the appendix's own table puts `31_past` (21), `35_natveg`
(18), `32_forestry` (17), `30_croparea` (16), `34_urban` (16), `29_cropland` (15) and
`09_drivers` (14) *above* `17_production` (12), and M56 is absent from it entirely. M10 (Owns
18 = the model maximum) and M11 (DependsOn 27) are correctly characterised; M17 (Reaches 12) is
correctly HIGH.

M56's importance is real but structural in a different way — it *declares* `vm_carbon_stock`,
which six modules write into — and that is what the guide should say instead of a centrality
tier its own table contradicts.

**Verify.**
```
$ python3 audit/tools/compute_module_centrality.py --table   # reproduces all 11 appendix rows exactly
$ python3 - <<'EOF'   # same definitions, applied to M56
… M56: owns 5 reaches 5 depends 13 ; rank by reaches = 22 of 46
EOF
```

**Fix.** Reword doc:11 to "four modules whose modification is highest-risk **for different
reasons** — M10 (largest owned reach, 18), M11 (largest inbound dependency, 27), M17
(production hub, reaches 12), M56 (declares `vm_carbon_stock`, written by six modules, and
prices it into the objective)", and change doc:450 to "**Centrality**: MEDIUM by reach (Owns 5
/ Reaches 5); critical by *inbound* coupling (DependsOn 13) and by objective-function leverage."
Add a pointer that 31/35/32/30/34/29 outrank M17 on reach and deserve the same care.

---

### B13 — Minor — `citation` — doc:1103 (Appendix B source line)

> "**Source**: Module_Dependencies.md §2.1 (lines 46-59)"

**Reality.** §2.1 "Most Connected Variables" starts at `core_docs/Module_Dependencies.md:80`
with its table at 84-94. Lines 46-59 are §1.2's `11_costs` paragraph and the Owns/Reaches
column definitions. The section anchor is right (so the reader recovers), only the line range
is stale — which is precisely the failure Appendix A documents and fixed by dropping line
numbers (doc:1082-1084). Minor, not Major, because the correct anchor travels alongside it.

**Verify.** `grep -n "#### 2.1 Most Connected Variables" core_docs/Module_Dependencies.md` → `80`.

**Fix.** Drop the parenthetical range: "**Source**: `core_docs/Module_Dependencies.md` §2.1".

---

## Deferred (unverified — no edit proposed)

- `vm_lu_transitions` described as "(gross between-type transitions)" (doc:47): the matrix
  includes the stay-diagonal (its row sums are `pcm_land` *totals*, not gross change); the
  diagonal-free quantities are `vm_landexpansion`/`vm_landreduction`. Arguably an acceptable
  compression — flagged for a human, not filed.
- "Centrality: HIGHEST in entire model" for M10 (doc:34): true on `Owns` (18 = model maximum),
  rank 2 on `Reaches` (`31_past` 21). Metric-ambiguous; the appendix shows both. Not filed.
- All `magpie4` R snippets (§1.5, §2.4, §3.5, §4.6, §5.2, §5.3): function existence and
  signatures (`land_transitions`, `water_avail`, `nr_inputs`, `nr_outputs`, `nr_soil_change`,
  `trade_balance`, `costs`) not checked against the version-pinned magpie4 clone this session.
  B4 is filed on the GAMS-side invariant only, which holds regardless.
- §2.4 cost-magnitude test: prose says "500-2000 billion" while the code tests `> 500 & < 5000`,
  and `vm_cost_glo` is in `mio. USD17MER/yr` — a probable unit/scale error, but it depends on
  what `magpie4::costs()` returns; not verified.
- §2.2 "Typical Magnitude (USD17/yr)" column: requires a GDX; not verifiable statically.
- `c56_pollutant_prices` range "0-1000+ USD/tCO2": lives in
  `modules/56_ghg_policy/input/f56_pollutant_prices.cs3`, not present in the worktree.
- §4.3 citation `input.gms:84-117` covers three of the four listed switches (84, 86, 90);
  `s56_c_price_induced_aff` is at 69 and *is* cited correctly at doc:535. Imprecise, below the
  bar for a bug.
- `core_docs/Module_Dependencies.md:178-180` ("17_production: 13 out, 1 in; 10_land: 15 out, 2
  in; 56_ghg_policy: 13 out, 3 in") disagrees with the role-map-derived 12/8, 18/5 and 5/13 —
  but that is a different document, outside this target.

---

## Method notes

- Every attribution claim was checked against `audit/integrated/depth_rolemap.json` first, then
  confirmed at both endpoints in code. One genuine map-vs-grep disagreement arose and the **map
  was right**: `vm_land` reaches `58_peatland` only through the macro form
  `m58_LandMerge(vm_land, vm_land_forestry,"j2")` (`modules/58_peatland/v2/equations.gms:23`), which
  a `vm_land(`/`vm_land.` grep misses entirely. Recorded because a future auditor running the
  narrow grep would "discover" a phantom consumer in this doc's §1.2 list.
- Absence claims (B6, B7) were each run with a positive control in the same directory.
- My independent reimplementation of Owns/Reaches/DependsOn reproduced all 11 published
  Appendix A rows and the `11_costs` footnote before being applied to M56 (B12).
