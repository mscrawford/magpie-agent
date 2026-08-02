# R60 depth audit — `cross_module/modification_safety_guide.md`

**Lens**: `citation_formula` (enter from file:line citations; equation-formula fidelity)
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec`
**Auditor**: adversarial depth-first, whole-tree greps, role map cross-check
**Date**: 2026-08-02

All code paths below are MAgPIE-repo-relative (`modules/NN_name/realization/file.gms:LINE`);
all doc paths are magpie-agent-repo-relative. Commands were run from the develop worktree
root unless noted.

---

## Headline

The doc's **quantitative spine is in good shape**. Every consumer/producer count in §1.2,
§3.2, Appendix A and Appendix B reproduces exactly against the code-derived role map and
against `audit/tools/compute_module_centrality.py --table`; the four Module-56 defaults, the
`q10_*` / `q11_*` / `q17_*` / `q56_*` equation names and formulas, the `pcm_land` and
`pm_prod_init` citations, and the "27 modules feed `q11_cost_reg`" claim all hold.

The failures cluster in three places the counting machinery does not reach:

1. **Prose about set scope** — §3.4 tells a developer that `vm_prod_reg` is plant-only. It is
   not: `q17_prod_reg` is declared over `k`, which contains five livestock commodities plus
   fish, wood and woodfuel, and the default `71_disagg_lvst` realization constrains
   `vm_prod(j,kli_*)` at cell level. This is the one Critical.
2. **Arrow direction in the ASCII diagrams** (§4.4, §5.1) — three separate `→`/`←→` claims
   assert edges the code does not have. Two of them contradict the doc's own cited source.
3. **Hand-maintained line ranges into sibling docs** — two point at materially different
   sections after those docs were restructured.

Everything that a checker computes is right; everything a human typed by hand around it is
where the bugs are.

---

## Bugs

### B1 — 🔴 Critical — `vm_prod_reg` claimed plant-only; `q17_prod_reg` covers livestock, fish and timber

**Doc** `modification_safety_guide.md:367-377`

> **❌ MISTAKE 1**: Forgetting that `vm_prod_reg` only covers PLANT commodities
> ```gams
> vm_prod_reg(i,"beef") = sum(cell(i,j), vm_prod(j,"beef"));
> * ERROR: Livestock modeled at regional level (Module 70), not cell level
> ```
> **✅ FIX**: Check commodity scope
> - **Module 17 handles**: Crops (kcr), pasture
> - **Module 70 handles**: Livestock (kli) — regional only

**Reality.** `modules/17_production/flexreg_apr16/equations.gms:10-11`:

```gams
q17_prod_reg(i2,k) ..
vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
```

`k` is declared in the default yields realization (`cfg$gms$yields <- "managementcalib_aug19"`,
`config/default.cfg:357`) at `modules/14_yields/managementcalib_aug19/sets.gms:12-16` and
contains `livst_rum, livst_pig, livst_chick, livst_egg, livst_milk, fish, wood, woodfuel`
alongside the crops. So the line the doc labels "WRONG" — regional livestock production as the
cell sum — **is literally what the code does**, for every `kli` member.

The cell-level livestock production it says does not exist is produced by the **default**
`71_disagg_lvst` realization (`foragebased_jul23`, `config/default.cfg:2221`):
`modules/71_disagg_lvst/foragebased_jul23/equations.gms:23` (`vm_prod(j2,kli_rum)`) and `:56`
(`vm_prod(j2,kli_mon) =l= ...`). Timber likewise:
`modules/73_timber/default/equations.gms:44,53` set `vm_prod(j2,"wood")` / `vm_prod(j2,"woodfuel")`.
`vm_prod` is declared `vm_prod(j,k)` — not `vm_prod(j,kcr)` — at
`modules/17_production/flexreg_apr16/declarations.gms:9`.

**Why Critical.** §3.4 is a "Common Mistakes" section aimed at someone about to modify
Module 17. Acting on it means either narrowing `q17_prod_reg` to crops (breaking every
livestock consumer of `vm_prod_reg` — 16, 18, 20, 21, 38, 50, 70, 71) or adding a second
regional aggregation path for livestock (double counting). Rubric trigger: "make a load-bearing
modification that breaks the model."

**Verify**
```
$ rg -n 'q17_prod_reg' modules/17_production/flexreg_apr16/equations.gms
10:q17_prod_reg(i2,k) ..
$ rg -n 'livst_rum' modules/14_yields/managementcalib_aug19/sets.gms
15:         foddr, pasture, cottn_pro, begr, betr, livst_rum, livst_pig,
$ rg -n 'vm_prod\(j2,kli' modules/71_disagg_lvst/foragebased_jul23/equations.gms
23:                  sum((kli_rum,kforage), vm_prod(j2,kli_rum)
56:                 vm_prod(j2,kli_mon) =l=
```

**Fix.** Replace MISTAKE 1 with the true scope boundary. `q17_prod_reg` runs over `k` (all
primary products incl. `kli`, `fish`, `wood`, `woodfuel`), *not* `kall` — the declared domain of
`vm_prod_reg` is `(i,kall)`, so the **secondary/processed** members of `kall`
(`oils, oilcakes, sugar, molasses, alcohol, ethanol, distillers_grain, brans, scp,
res_*`) are the ones `q17_prod_reg` does **not** define; those slices are populated by
18_residues, 20_processing and 21_trade. State the real per-commodity producers of `vm_prod`
(30_croparea crops, 31_past pasture, 71_disagg_lvst livestock, 73_timber wood) instead of
"Module 70 handles livestock — regional only".

---

### B2 — 🟠 Major — "Production-Yield-Livestock Triangle" has no `17 → 14` and no `14 ↔ 70` edge

**Doc** `modification_safety_guide.md:611-614`

> 1. **Production-Yield-Livestock Triangle**:
>    ```
>    17_production ←→ 14_yields ←→ 70_livestock ←→ 17_production
>    ```

**Reality.** 17_production declares exactly three interface objects — `vm_prod`, `vm_prod_reg`
(`.../declarations.gms:9-10`) and `pm_prod_init` (`:18`). **14_yields references none of them.**
The only edge between the two is the reverse one: 17 reads 14's `pm_yields_semi_calib`
(declared `modules/14_yields/managementcalib_aug19/declarations.gms:19`) at
`modules/17_production/flexreg_apr16/presolve.gms:10`. Direction is **14 → 17, unidirectional**.

`14 ↔ 70` has no direct edge in either direction: 70_livestock references neither `vm_yld` nor
`pm_yields_semi_calib`, and 14_yields references no 70 interface. `70 ↔ 17` is likewise
one-way — 70 reads `vm_prod_reg` (`modules/70_livestock/fbask_jan16/equations.gms:18`) and 17
reads nothing 70 declares.

**Verify** (rg + grep, with positive controls, each probe standalone)
```
$ rg -n 'vm_prod|pm_prod_init' modules/14_yields/          -> exit 1, no output
$ grep -rn 'vm_prod' modules/14_yields/                    -> no match
$ rg -c 'vm_yld' modules/14_yields/ | head -5              -> 5 files match (positive control OK)
$ grep -rn 'vm_yld\|pm_yields_semi_calib' modules/70_livestock/   -> no match
$ grep -rn 'vm_prod_reg' modules/70_livestock/ | head -3   -> 3 matches (positive control OK)
$ rg -n 'pm_yields_semi_calib' modules/17_production/flexreg_apr16/presolve.gms
10:pm_prod_init(j,kcr)=sum(w,fm_croparea("y1995",j,w,kcr)*pm_yields_semi_calib(j,kcr,w));
```

**Note.** The claim is inherited verbatim from `core_docs/Module_Dependencies.md:188-194`, so
this is a latent doc bug in **both** files (rubric §1 `doc_error_answerer_beat_it` mandate).
Fix both or the pointer re-imports it.

**Fix.** Draw the actual edges: `14_yields → 17_production` (`pm_yields_semi_calib`,
presolve-time) and `17_production → 70_livestock` (`vm_prod_reg`). The yield↔production
feedback in MAgPIE closes through `30_croparea` (which reads `vm_yld` and writes `vm_prod`,
`modules/30_croparea/simple_apr24/equations.gms:15`) and `13_tc`, not through 17 or 70
directly. If the intent is a behavioural loop rather than an interface loop, label it as such.

---

### B3 — 🟠 Major — `35_natveg ←→ 22_land_conservation` drawn bidirectional; the edge is one-way

**Doc** `modification_safety_guide.md:627-630`

> 2. **Land-Vegetation Bidirectional**:
>    ```
>    10_land ←→ 35_natveg ←→ 22_land_conservation
>    ```

**Reality.** 22 → 35 exists: `pm_land_conservation(t,j,land,consv_type)` is declared and
populated in `modules/22_land_conservation/area_based_apr22/declarations.gms:15` /
`presolve_ini.gms:54`, and read by 35 at
`modules/35_natveg/pot_forest_may24/presolve.gms:149,162,174,177,179`. The reverse edge does
not exist — 22_land_conservation contains **zero** references to any of the six interfaces
35_natveg declares.

The doc's own cited source says so explicitly (`core_docs/Module_Dependencies.md:198-200`):
"`22_land_conservation → 35_natveg (unidirectional: pm_land_conservation)`" and
"`10_land → 22_land_conservation (unidirectional: vm_land)`". The target doc collapsed a
labelled-unidirectional pair into a `←→` chain.

**Verify**
```
$ rg -n '^\s*(vm_|pm_|im_)\w+' modules/35_natveg/pot_forest_may24/declarations.gms
   -> pm_max_forest_est, vm_land_other, vm_landdiff_natveg, vm_prod_natveg,
      vm_cost_hvarea_natveg, vm_natforest_reduction
$ for v in pm_max_forest_est vm_land_other vm_landdiff_natveg vm_prod_natveg \
           vm_cost_hvarea_natveg vm_natforest_reduction; do
      grep -rc "$v" modules/22_land_conservation/ | awk -F: '{s+=$2} END{print s+0}'; done
   -> 0 0 0 0 0 0
$ grep -rn 'pm_land_conservation' modules/22_land_conservation/ | head -3   (positive control)
   -> module.gms:17, area_based_apr22/declarations.gms:15, presolve_ini.gms:54
```

**Fix.** `10_land ←→ 35_natveg` (keep), plus two one-way arrows:
`22_land_conservation → 35_natveg` (`pm_land_conservation`) and
`10_land → 22_land_conservation` (`vm_land`).

---

### B4 — 🟠 Major — "CDR Rewards → 32_forestry": 32 reads nothing from 56; the interface runs 32 → 56

**Doc** `modification_safety_guide.md:496-497`

> ```
>    ├─ CDR Rewards → 32_forestry (afforestation incentive)
>    │     └─ Affects land competition (forest vs. crop)
> ```

**Reality.** `vm_reward_cdr_aff(i)` is declared and populated in 56
(`modules/56_ghg_policy/price_aug22/declarations.gms:43`, `equations.gms:67-70`) and read by
exactly two modules — 11_costs (`modules/11_costs/default/equations.gms:27`,
`- vm_reward_cdr_aff(i2)`) and 56 itself. **32_forestry contains no reference to
`vm_reward_cdr_aff`, `im_pollutant_prices`, or any `s56_*` / `p56_*` object.**

The real interface points the other way: 32 declares and populates `vm_cdr_aff(j,ac,aff_effect)`
(`modules/32_forestry/dynamic_may24/declarations.gms:83`, `equations.gms:37`), which **56**
reads in `q56_reward_cdr_aff` (`modules/56_ghg_policy/price_aug22/equations.gms:77`). The
afforestation incentive reaches 32 only through the objective function — the reward term
changes the shadow price on `vm_cdr_aff` — not through any variable 32 reads. Same shape as the
R51 anchor ("M52 routes to M56" was wrong; M56 reads `vm_carbon_stock` directly).

**Verify**
```
$ rg -n 'vm_reward_cdr_aff|im_pollutant_prices|s56_|p56_' modules/32_forestry/
   -> RG_EXIT=1 (no matches)
$ grep -rn 'im_pollutant_prices' modules/32_forestry/    -> no match
$ rg -n 'vm_cdr_aff' modules/32_forestry/ | head -8      -> 8 matches (positive control OK)
$ rg -n 'vm_cdr_aff' modules/56_ghg_policy/price_aug22/equations.gms
77:               (sum(aff_effect,(1-s56_buffer_aff)*vm_cdr_aff(j2,ac,aff_effect)) * ...
```

**Fix.** Redraw as:
`32_forestry --vm_cdr_aff--> 56_ghg_policy --vm_reward_cdr_aff--> 11_costs --objective--> 32_forestry`,
and say in words that 32 responds to the reward *through the objective*, holding no direct
interface to 56.

---

### B5 — 🟠 Major — `c56_emis_policy` "60+ policies"; the `scen56` set has 44

**Doc** `modification_safety_guide.md:482`

> | `c56_emis_policy` | reddnatveg_nosoil | 60+ policies | Which emissions priced |

**Reality.** `scen56` (`modules/56_ghg_policy/price_aug22/sets.gms:119`) has **44** members.
`c56_emis_policy` selects a row of `f56_emis_policy(scen56,pollutants_all,emis_source)`
(`input.gms:113`), so 44 is the option count. The doc's own cited source already says 44:
`modules/module_56.md:37` — "| `c56_emis_policy` | ... | reddnatveg_nosoil | 44 policies |".

(The sibling claim "100+ IAM scenarios" for `c56_pollutant_prices` **is** correct: `ghgscen56`
has 102 members, plus `coupling` and `emulator`.)

**Verify**
```
$ python3 -c "import re; t=open('modules/56_ghg_policy/price_aug22/sets.gms').read(); \
  m=re.search(r'\n\s*scen56[^/]*?/(.*?)/', t, re.S); \
  print(len([x for x in m.group(1).replace(chr(10),' ').split(',') if x.strip()]))"
44
$ python3 -c "... same for ghgscen56 ..."
102
```

**Fix.** `60+ policies` → `44 policies (scen56 set)`.

---

### B6 — 🟠 Major — Transition Matrix Test asserts `row_sums == col_sums`; the code makes them `pcm_land` vs `vm_land`

**Doc** `modification_safety_guide.md:146-153`

> 2. **Transition Matrix Test**:
>    ```r
>    # Verify row sums = column sums
>    transitions <- land_transitions(gdx)
>    row_sums <- dimSums(transitions, dim="to")
>    col_sums <- dimSums(transitions, dim="from")
>    stopifnot(all(abs(row_sums - col_sums) < 1e-6))
>    ```

**Reality.** `modules/10_land/landmatrix_dec18/equations.gms:19-25`:

```gams
 q10_transition_to(j2,land_to) ..
  sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e= vm_land(j2,land_to);

 q10_transition_from(j2,land_from) ..
  sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);
```

Summing out `to` yields a vector indexed by `land_from` that equals **`pcm_land`**; summing out
`from` yields a vector indexed by `land_to` that equals **`vm_land`**. Comparing them
element-wise asserts `pcm_land(x) == vm_land(x)` for every land type — i.e. that no land-use
change occurred. The test in a "MUST pass all" suite therefore fails on any run that does
anything. Only the *grand totals* are equal (`q10_land_area`, `equations.gms:13-15`).

The doc states the correct relations two sections earlier, at lines 108-110 — this is an
internal contradiction, not a missing fact.

**Verify**
```
$ sed -n '13,25p' modules/10_land/landmatrix_dec18/equations.gms   (as quoted above)
```

**Fix.**
```r
# Row sums (over land_to)  == previous-timestep land
# Col sums (over land_from) == current land
stopifnot(all(abs(dimSums(transitions, dim="to")   - pcm_land_prev) < 1e-6))
stopifnot(all(abs(dimSums(transitions, dim="from") - land_current)  < 1e-6))
# grand totals only:
stopifnot(abs(sum(dimSums(transitions, dim="to")) - sum(dimSums(transitions, dim="from"))) < 1e-6)
```

---

### B7 — 🟠 Major — Debugging fix inverts the transition-matrix index: `sum(land_from, …) = pcm_land`

**Doc** `modification_safety_guide.md:827`

> 2. Verify transition matrix: `sum(land_from, vm_lu_transitions) = pcm_land`

**Reality.** Inverted. `sum(land_from, vm_lu_transitions(j,land_from,land_to)) =e= vm_land(j,land_to)`
(`q10_transition_to`, `modules/10_land/landmatrix_dec18/equations.gms:19-21`). It is
`sum(land_to, …)` that equals `pcm_land(j,land_from)` (`q10_transition_from`, `:23-25`). The
doc gets it right at line 109 and wrong here, in the emergency-debugging section a reader
reaches while the model is already infeasible.

**Verify** — same `sed -n '13,25p' modules/10_land/landmatrix_dec18/equations.gms`.

**Fix.** `sum(land_to, vm_lu_transitions(j,land_from,land_to)) = pcm_land(j,land_from)`
(and optionally add the `sum(land_from, …) = vm_land(j,land_to)` companion).

---

### B8 — 🟠 Major — "✅ SAFE" snippet uses a non-existent `land` member and the wrong arity for `pm_land_conservation`

**Doc** `modification_safety_guide.md:172-175`

> **✅ SAFE**: Adding new constraints on existing transitions
> ```gams
> vm_lu_transitions.fx(j,"forest","crop")$(pm_land_conservation(j,"forest") > 0) = 0;
> ```

**Reality.** Two independent compile failures in one line advertised as safe:

- `"forest"` is not a member of `land`. `core/sets.gms:250-251`:
  `land Land pools / crop, past, forestry, primforest, secdforest, urban, other /`.
  (The doc itself states "7 land types" at line 40 and lists them correctly at line 87.)
  → GAMS `$170`/`$171` domain violation.
- `pm_land_conservation` is **4-dimensional**:
  `pm_land_conservation(t,j,land,consv_type)`
  (`modules/22_land_conservation/area_based_apr22/declarations.gms:15`). The snippet passes 2.

The same phantom label appears at line 121 (`vm_land.fx(j,"forest") = 50;`) inside a ❌ WRONG
example — there it is incidental, but it reinforces the wrong member name.

**Verify**
```
$ rg -n 'land Land pools' -A2 core/sets.gms
250:  land Land pools
251-        / crop, past, forestry, primforest, secdforest, urban, other /
$ rg -n 'pm_land_conservation' modules/*/*/declarations.gms
modules/22_land_conservation/area_based_apr22/declarations.gms:15: pm_land_conservation(t,j,land,consv_type) ...
```

**Fix.**
```gams
vm_lu_transitions.fx(j,"primforest","crop")$(pm_land_conservation(t,j,"primforest","protect") > 0) = 0;
```
and change `"forest"` → `"secdforest"` (or `"primforest"`) at line 121.

---

### B9 — 🟠 Major — Appendix B lists 17_production as the **Producer** of `vm_prod`; 17 declares it, four other modules populate it

**Doc** `modification_safety_guide.md:1097`

> | `vm_prod(j,k)` | 8 | 17_production | vm_ | Cell-level production |

**Reality.** 17_production **DECLARES** `vm_prod(j,k)`
(`modules/17_production/flexreg_apr16/declarations.gms:9`) and **READS** it on the RHS of
`q17_prod_reg` (`equations.gms:11`). It never determines it. The equation-level populators are:

| module | site |
|---|---|
| 30_croparea | `simple_apr24/equations.gms:15` — `vm_prod(j2,kcr) =e= sum(w, vm_area*vm_yld)` |
| 31_past | `endo_jun13/equations.gms:17` — `vm_prod(j2,"pasture") =l= ...` |
| 71_disagg_lvst | `foragebased_jul23/equations.gms:23,56` — `kli_rum` / `kli_mon` |
| 73_timber | `default/equations.gms:44,53` — `"wood"` / `"woodfuel"` |

The only thing 17 writes is a **solution-level starting point** in the first timestep:
`vm_prod.l(j,kcr) = pm_prod_init(j,kcr)` (`flexreg_apr16/presolve.gms:15`, active because
`cfg$gms$c17_prod_init <- "on"`, `config/default.cfg:620`) — an initialization, not a
determination.

This is the DECLARED-vs-POPULATED conflation AGENT.md flags as the highest-propagation defect
class. Note the doc gets it *right* in prose at line 353 ("Module 30 (Croparea) → `vm_prod(j,k)`
→ Module 17"), so the table contradicts the body. The 8-consumer **count** is correct.

`core_docs/Module_Dependencies.md:89` carries the same "17_production → multiple" attribution —
fix both.

**Verify**
```
$ python3 -c "import json; d=json.load(open('audit/integrated/depth_rolemap.json')); print(d['vm_prod'])"
{'declared_in': '17_production', 'populated_by': ['30','31','71','73'],
 'read_by': ['17','18','31','38','40','42','71','73']}
$ rg -n 'vm_prod\(' modules/30_croparea/*/equations.gms modules/31_past/*/equations.gms   (confirms)
$ rg -n 'vm_prod' modules/17_production/flexreg_apr16/presolve.gms
15:vm_prod.l(j,kcr) = pm_prod_init(j,kcr);
```

**Fix.** Split the column, or annotate:
`vm_prod(j,k) | 8 | declared 17_production; populated 30_croparea (kcr), 31_past (pasture),
71_disagg_lvst (kli), 73_timber (wood/woodfuel) | vm_ | Cell-level production`.
(The other five rows are clean: `vm_land`←10, `im_pop_iso`←09, `pm_interest`←12,
`vm_prod_reg`←17, `vm_area`←30 all declare *and* populate.)

---

### B10 — 🟠 Major — Citation drift: `Module_Dependencies.md:151-179` is Hub-and-Spoke, not Critical Feedback Cycles

**Doc** `modification_safety_guide.md:609`

> **Critical Feedback Cycles** (from Module_Dependencies.md:151-179):

**Reality.** `core_docs/Module_Dependencies.md` §4.1 *Critical Feedback Cycles* starts at
**line 184** and runs to ~217. Lines 151-179 contain the tail of §3.1 *Architectural Layers*
(Layers 4-6) and all of §3.2 *Hub-and-Spoke Patterns* (Pure Sources / Pure Sinks / Central
Hubs) — materially different content.

**Verify**
```
$ rg -n '^#{1,4} ' core_docs/Module_Dependencies.md | sed -n '12,15p'
166:#### 3.2 Hub-and-Spoke Patterns
182:### 4. Circular Dependencies (Feedback Loops)
184:#### 4.1 Critical Feedback Cycles
218:#### 4.2 Dependency Chains
```

**Fix.** `(from Module_Dependencies.md § 4.1 Critical Feedback Cycles)` — cite by section, as
Appendix A already does for exactly this reason.

---

### B11 — 🟠 Major — Citation drift: `Module_Dependencies.md §2.1 (lines 46-59)` — §2.1 is at 80-97

**Doc** `modification_safety_guide.md:1103`

> **Source**: Module_Dependencies.md §2.1 (lines 46-59)

**Reality.** §2.1 *Most Connected Variables* is at `core_docs/Module_Dependencies.md:80-97`.
Lines 46-59 are the tail of §1.2 *Module Centrality Rankings* — the `11_costs` footnote and the
"Reading the two columns" prose. The **section label is right**; the line numbers are stale.
(Appendix B's six counts do match the §2.1 table at 86-91, so only the pointer is wrong.)

**Verify**
```
$ rg -n '^#{1,4} ' core_docs/Module_Dependencies.md | grep '2.1'
80:#### 2.1 Most Connected Variables
$ sed -n '46,59p' core_docs/Module_Dependencies.md   -> "**`11_costs` is deliberately not a row.** ..."
```

**Fix.** Drop the line range: `**Source**: Module_Dependencies.md § 2.1 Most Connected Variables`.

---

### B12 — 🟡 Minor — Switch-table citation `input.gms:84-117` does not contain `s56_c_price_induced_aff`

**Doc** `modification_safety_guide.md:477-484`

> **Configuration Switches** (modules/56_ghg_policy/price_aug22/input.gms:84-117):
> … | `s56_c_price_induced_aff` | 1 (ON) | 0/1 | Enable afforestation CDR |

**Reality.** `modules/56_ghg_policy/price_aug22/input.gms:84-117` is the `$setglobal` block plus
the `table`/`$include` statements — it holds `c56_pollutant_prices` (:84),
`c56_emis_policy` (:86) and `c56_carbon_stock_pricing` (:90), but **not**
`s56_c_price_induced_aff`, which is a scalar at **`input.gms:69`** (the doc itself cites :69
correctly at line 535). File is 117 lines, so the range is in-bounds; it is the scope that is
wrong for one of the four rows.

All four **default values are correct** in both `input.gms` and `config/default.cfg`
(`:1734`, `:1831`, `:1838`, `:1762`).

**Verify**
```
$ sed -n '69p;84p;86p;90p' modules/56_ghg_policy/price_aug22/input.gms
  s56_c_price_induced_aff   Switch for C price driven re-afforestation (1=on 0=off) / 1 /
$setglobal c56_pollutant_prices  R34M410-SSP2-NPi2025
$setglobal c56_emis_policy  reddnatveg_nosoil
$setglobal c56_carbon_stock_pricing  actualNoAcEst
```

**Fix.** `(modules/56_ghg_policy/price_aug22/input.gms:64-90 — scalars at :64-82, $setglobals at :84-90)`.

---

### B13 — 🟡 Minor — `carbon_balance_conservation.md:450-550` cited for "carbon-policy interactions"; 450-505 is Chapman-Richards forest growth

**Doc** `modification_safety_guide.md:507`

> See: `cross_module/carbon_balance_conservation.md:450-550` for full carbon-policy interactions

**Reality.** In `cross_module/carbon_balance_conservation.md`: §6 *Chapman-Richards Growth for
Forests* spans 444-505 (§6.1 growth equation, §6.2 climate parameters, §6.3 trajectories);
§7 *Module Interactions for Carbon Balance* starts at 506, and the cited range clips only
§7.1 (Module 52) and part of §7.2 (Module 59). There is no §7.x for 56_ghg_policy at all. The
carbon-**policy** content lives in §4 *CO₂ Emission Calculation* (274-364) and §8.2
*Afforestation Scenario* (662-694).

**Verify**
```
$ rg -n '^#{2,4} ' cross_module/carbon_balance_conservation.md | sed -n '20,27p'
444:## 6. Chapman-Richards Growth for Forests
446:### 6.1 Vegetation Carbon Growth Equation
...
506:## 7. Module Interactions for Carbon Balance
```

**Fix.** `See: cross_module/carbon_balance_conservation.md § 4 (CO₂ Emission Calculation) and
§ 8.2 (Afforestation Scenario)`.

---

### B14 — 🟡 Minor — "Centrality: **HIGHEST** in entire model" for Module 10 contradicts the doc's own Appendix A

**Doc** `modification_safety_guide.md:34`

> **Centrality**: **HIGHEST** in entire model

**Reality.** Appendix A of the same file — regenerated from
`audit/tools/compute_module_centrality.py --table`, which is ranked by `Reaches` — puts
**31_past first at 21**, with 10_land second at 18. 10_land *is* first on `Owns` (18), so the
claim is true under one column and false under the ranking column the appendix uses. Unqualified
"HIGHEST in entire model" reads as contradicted eleven hundred lines later.

**Verify**
```
$ python3 audit/tools/compute_module_centrality.py --table | sed -n '3,5p'
| 1 | **31_past** | 1 | 21 | +20 | 13 | Pasture area and production |
| 2 | **10_land** | 18 | 18 | 0 | 5 | Core land allocation |
| 3 | **35_natveg** | 5 | 18 | +13 | 10 | Natural vegetation |
```
(Every other Appendix A cell — all 11 rows × Owns/Reaches/gap/DependsOn, the risk-band rule
🔴 ≥18 / 🟠 ≥12 / 🟡 below, the ⚠ gap ≥ +10 marks, and the `11_costs` "owns 1 / reaches 1 /
depends on 27" footnote — reproduces exactly.)

**Fix.** "**Centrality**: highest `Owns` in the model (18 modules read variables 10_land
declares); second on `Reaches` behind 31_past (21) — see Appendix A."

---

### B15 — 🟡 Minor — `vm_lu_transitions` described as "gross between-type transitions"; it includes the diagonal

**Doc** `modification_safety_guide.md:47`

> | `vm_lu_transitions(j,land_from,land_to)` | 3 modules | 🟠 HIGH | Transition matrix (gross between-type transitions) |

**Reality.** `vm_lu_transitions` is the **full** transition matrix including land that stays in
its own type: `q10_transition_from` sums it over `land_to` to `pcm_land(j,land_from)`, the
entire previous stock (`modules/10_land/landmatrix_dec18/equations.gms:23-25`). The
*between-type* (gross) flows are `vm_landexpansion` / `vm_landreduction`, which exclude the
diagonal explicitly: `$(not sameas(land_from,land_to))` at `equations.gms:32` and `:37`.

**Verify** — `sed -n '19,38p' modules/10_land/landmatrix_dec18/equations.gms`.

**Fix.** "Full transition matrix incl. same-type persistence (diagonal); gross between-type
flows are `vm_landexpansion` / `vm_landreduction`."

---

### B16 — 🟡 Minor — "affects Module 29, 30, 32, 35" for transition costs; the only direct consumer of either cost variable is 11_costs

**Doc** `modification_safety_guide.md:177-181`

> **✅ SAFE**: Modifying transition costs (affects Module 29, 30, 32, 35)
> ```gams
> vm_cost_landcon.up(j,"primforest") = 1e6;  * USD/ha
> ```

**Reality.** Module 10's transition cost is `vm_cost_land_transition(j)`
(`modules/10_land/landmatrix_dec18/equations.gms:42-44`, `q10_cost`), read only by 11_costs
(`modules/11_costs/default/equations.gms:41`). The variable in the snippet,
`vm_cost_landcon(j,land)`, belongs to **39_landconversion** and is likewise read only by
11_costs (`equations.gms:20`). Neither is referenced by 29, 30, 32 or 35 — those modules
respond only through the objective function, transitively.

(The snippet's own syntax is valid: `vm_cost_landcon(j,land)`, `"primforest"` ∈ `land`.)

**Verify**
```
$ python3 -c "import json;d=json.load(open('audit/integrated/depth_rolemap.json'));\
  print(d['vm_cost_land_transition']); print(d['vm_cost_landcon'])"
{'declared_in':'10_land','populated_by':['10'],'read_by':['10','11']}
{'declared_in':'39_landconversion','populated_by':['39'],'read_by':['11','39']}
```

**Fix.** "affects the objective via 11_costs only; 29/30/32/35 respond indirectly through the
optimum, and hold no direct reference to `vm_cost_land_transition` or `vm_cost_landcon`."

---

### B17 — 🟢 Informational — empty inline code span in §8.3

**Doc** `modification_safety_guide.md:1041`

> 2. Search `` documentation

An empty backtick pair where a target used to be — most likely a path removed by the public-repo
path-hygiene pass. **Fix**: "Search the `modules/` and `core_docs/` documentation".

---

## Verified-clean (checked and correct — recorded so a later round need not re-derive)

**Citations, all `test -f` + in-range + token-present:**
`modules/10_land/landmatrix_dec18/postsolve.gms:8-9` (`pcm_land(j,land) = vm_land.l(j,land);`, file 64 lines) ·
`modules/17_production/flexreg_apr16/presolve.gms:10` (`pm_prod_init` formula **character-exact**
to doc line 392, file 18 lines) ·
`modules/56_ghg_policy/price_aug22/input.gms:69` (`s56_c_price_induced_aff … / 1 /`) ·
`modules/57_maccs/on_aug22/preloop.gms:24-25` (`i57_mac_step_n2o` / `i57_mac_step_ch4` from
`im_pollutant_prices`) ·
`cross_module/nitrogen_food_balance.md:229-250` (§2.7 Food Balance Check) ·
`modules/module_11.md` 84-115 (q11_cost_reg block, actual 86-118) ·
`modules/module_56.md` 32-42 (switch table) and 79-101 (§2.2 q56_emis_pricing_co2).

**Realization names** (`ls -d modules/NN_*/*/`): `landmatrix_dec18`, `default` (11), `flexreg_apr16`,
`price_aug22`, `on_aug22` — all real, all match `config/default.cfg`.

**Formulas:** `q10_land_area` (strict `=e=` over `land`) · row/column sum statements at doc
lines 109-110 (**correct**, unlike 827) · `q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2))` ·
`q11_cost_reg` structure incl. `- vm_reward_cdr_aff(i2)` · `q17_prod_reg` ·
`q56_emission_costs` · `q56_emis_pricing_co2` uses `(pcm_carbon_stock − vm_carbon_stock)` in
that order (doc line 546 correct) · units `mio. USD17MER per yr` (11_costs/declarations.gms:9-10).

**Counts** (role map + both-endpoint greps): `vm_land` 10 and the exact member list
22/29/30/31/32/34/35/50/58/59 · `vm_lu_transitions` 3 · `vm_landexpansion` 4 ·
`vm_landreduction` 2 · `pcm_land` 12 · the 18-module union at doc line 58 (member-exact; 14_yields
enters via `pm_land_hist`/`pm_land_start`, read in `modules/14_yields/managementcalib_aug19/preloop.gms`) ·
the 11-module set at doc line 157 · `vm_prod_reg` 8 = {16,18,20,21,38,50,70,71} · `pm_prod_init` 1 = {38} ·
`vm_emission_costs` = {11_costs, 15_food} with 15 reading `vm_emission_costs.l(i)` at
`modules/15_food/anthro_iso_jun22/intersolve.gms:23` for `p15_tax_recycling` (doc's parenthetical
is exactly right) · `vm_reward_cdr_aff` = {11_costs} · `im_pollutant_prices` = {57_maccs}, dims
`(t_all,i,pollutants,emis_source)` character-exact · Appendix B's six counts (10/10/9/8/8/8) ·
**"27 modules"** — independently re-derived by mapping all 32 `vm_*` terms in `q11_cost_reg` to
their declaring module: exactly 27 distinct modules.

**Defaults** (code + `config/default.cfg`): `c56_pollutant_prices` R34M410-SSP2-NPi2025 ·
`c56_emis_policy` reddnatveg_nosoil · `c56_carbon_stock_pricing` actualNoAcEst {actual,
actualNoAcEst} · `s56_c_price_induced_aff` 1 · "100+ IAM scenarios" (`ghgscen56` = 102).

**Cost-variable attributions** (doc §2.2 table, all 7 rows): `vm_cost_prod_crop`→38_factor_costs ·
`vm_cost_prod_past`→31_past · `vm_cost_prod_livst`→70_livestock ·
`vm_nr_inorg_fert_costs`→50_nr_soil_budget · `vm_emission_costs`→56_ghg_policy ·
`vm_cost_landcon`→39_landconversion · `vm_cost_trade_{tariff,margin,feasibility}`→21_trade.

**Appendix A**: all 11 rows reproduce byte-for-byte against
`python3 audit/tools/compute_module_centrality.py --table`, including the tie note and the
`11_costs` footnote; the stated risk-band rule and every ⚠ mark are self-consistent with the
table.

---

## Deferred (not verified; no edit proposed)

- All `magpie4` R snippets (`land_transitions()`, `nr_inputs()`, `nr_outputs()`,
  `nr_soil_change()`, `water_avail()`, `land_conservation()`, `trade_balance()`): existence and
  signatures not checked against the renv-pinned magpie4 clone — outside this lens.
- Magnitude ranges in §2.2 (e.g. `vm_cost_prod_crop` "~100-500 billion") and §2.4
  ("500-2000 billion USD17/yr", with a `stopifnot` upper bound of 5000 that does not match the
  prose): require a GDX; not checkable from source.
- §5.1's "26 circular dependencies" total and §5.1 cycle 4 (the 5-module Forest-Carbon chain):
  inherited from `Module_Dependencies.md`; a full cycle enumeration was out of scope after the
  two cycles above were falsified. Worth its own pass.
- Doc line 184 "Requires updating 20+ files across model" for a land-type change: plausible but
  not counted.
- §3.4's "Module 73 handles: Timber — special aggregation": 73 writes `vm_prod(j,"wood"/"woodfuel")`
  and `q17_prod_reg` aggregates them like any other `k` member, so "special aggregation" looks
  wrong too — but it is subsumed by B1's rewrite and not scored separately.
