# R60 depth audit — `cross_module/modification_safety_guide.md`

**Lens**: `config_realization` (entry from `config/default.cfg` + realization directory listings;
priority on default values, `cfg$gms$*` switch behaviour, realization names, and which realization
is DEFAULT)
**Ground truth**: MAgPIE `develop` read-only worktree (HEAD `2c02843ec`)
**Attribution reference**: `audit/integrated/depth_rolemap.json` (checked first for every
DECLARED/POPULATED/READ claim, then confirmed with a both-endpoints exact-token grep)
**Claims verified**: ~110 code-checkable claims
**Bugs**: 18 (1 Critical, 8 Major, 8 Minor, 1 Informational) — all confirmed with reproducible commands

> All commands below are run from the root of the `develop` worktree unless noted.
> `rg -P` (PCRE2) is required for the exact-token patterns: `rg`'s default engine has no look-around,
> and a bare substring grep for `vm_land` silently also matches `vm_landexpansion`,
> `vm_landreduction`, `vm_landdiff` (this is the mechanism behind BUG-11).

---

## What the lens found CLEAN (recorded so a later round does not re-litigate)

The doc has clearly been through prior repair rounds. Under this lens the following are **correct**:

| Claim | Verdict |
|---|---|
| `modules/10_land/landmatrix_dec18/`, `modules/11_costs/default/`, `modules/17_production/flexreg_apr16/`, `modules/56_ghg_policy/price_aug22/` | ✅ all four are the **only** realization dir in their module → trivially the default; no non-default-as-active error anywhere in the doc |
| `c56_pollutant_prices` def `R34M410-SSP2-NPi2025` | ✅ `config/default.cfg:1734` + `modules/56_ghg_policy/price_aug22/input.gms:84` |
| `c56_emis_policy` def `reddnatveg_nosoil` | ✅ `config/default.cfg:1831` + `input.gms:86` |
| `c56_carbon_stock_pricing` def `actualNoAcEst`, options `actual / actualNoAcEst` | ✅ `input.gms:90-91` (note: `config/default.cfg:1838` is missing its `cfg$gms$` prefix — an upstream MAgPIE quirk, not a doc bug; the effective default is unchanged) |
| `s56_c_price_induced_aff` = 1 (ON) | ✅ `input.gms:69` `/ 1 /`, `config/default.cfg:1762` |
| `input.gms:69` cited for `s56_c_price_induced_aff` (doc:535) | ✅ exact |
| `modules/57_maccs/on_aug22/preloop.gms:24-25` = MAC step sizing from `im_pollutant_prices` | ✅ exact (`i57_mac_step_n2o` / `i57_mac_step_ch4`) |
| `im_pollutant_prices(t_all,i,pollutants,emis_source)` | ✅ `modules/56_ghg_policy/price_aug22/declarations.gms:9` |
| `vm_emission_costs` consumers = `11_costs`, `15_food` (+ "food-tax recycling in intersolve.gms") | ✅ `modules/15_food/anthro_iso_jun22/intersolve.gms:23` |
| `vm_reward_cdr_aff` consumer = `11_costs` | ✅ |
| `im_pollutant_prices` consumer = `57_maccs` | ✅ |
| `vm_land` 10 consumers, list `22,29,30,31,32,34,35,50,58,59` | ✅ exact-token grep reproduces the list exactly |
| `vm_lu_transitions` 3 / `vm_landexpansion` 4 / `vm_landreduction` 2 / `pcm_land` 12 | ✅ all four reproduce |
| the 18-module union (doc:58) | ✅ reproduces exactly, incl. `11_costs` (via `vm_cost_land_transition`) and `14_yields` (via `pm_land_start`) |
| the 11-module set at doc:157 ("10 vm_land consumers plus 39_landconversion") | ✅ reproduces |
| `vm_prod_reg` 8 consumers = `16,18,20,21,38,50,70,71`; `pm_prod_init` → `38_factor_costs` only | ✅ (and `factor_costs` default is `sticky_feb18`, which **is** a `pm_prod_init` reader — no capability-vs-default gap) |
| Appendix B counts: `vm_land` 10, `im_pop_iso` 10, `pm_interest` 9, `vm_prod` 8, `vm_prod_reg` 8, `vm_area` 8, all producers | ✅ all reproduce |
| §2.2 "27 modules" + all 7 cost-variable→module attributions | ✅ 32 cost terms in `q11_cost_reg` resolve to exactly 27 distinct declaring modules |
| `pcm_land` assignment at `modules/10_land/landmatrix_dec18/postsolve.gms:8-9` | ✅ (line 9 is the statement, line 8 its comment) |
| `pm_prod_init` init at `modules/17_production/flexreg_apr16/presolve.gms:10` incl. the exact formula | ✅ character-for-character |
| §1.4 row/column sum rules (doc:109-110) | ✅ match `q10_transition_from` / `q10_transition_to` |
| `q56_emis_pricing_co2` uses `(pcm_carbon_stock - vm_carbon_stock)` | ✅ `modules/56_ghg_policy/price_aug22/equations.gms:22` |
| `q10_land_area`, `q11_cost_glo`, `q11_cost_reg`, `v11_cost_reg`, `vm_cost_timber`, `vm_emissions_reg` | ✅ all exist as named |
| Appendix A: every `Owns/Reaches/gap/DependsOn` number, all 11 rows, the ⚠ gap≥+10 marks, the risk bands, and the `11_costs` footnote | ✅ reproduce byte-for-byte from `python3 audit/tools/compute_module_centrality.py --table` |
| `c56_pollutant_prices` "100+ IAM scenarios" | ✅ `ghgscen56` has 102 members |
| citations to `modules/module_11.md:84-115`, `modules/module_56.md:32-42`, `modules/module_56.md:79-101`, `cross_module/nitrogen_food_balance.md:229-250` | ✅ all land on the promised content |

---

## BUG-01 — Critical — `mechanism`

**doc**: `modification_safety_guide:367` (§3.4 MISTAKE 1, block spans 367-378)

> **❌ MISTAKE 1**: Forgetting that `vm_prod_reg` only covers PLANT commodities
> `vm_prod_reg(i,"beef") = sum(cell(i,j), vm_prod(j,"beef"));`
> `* ERROR: Livestock modeled at regional level (Module 70), not cell level`
> **✅ FIX**: … **Module 17 handles**: Crops (kcr), pasture — **Module 70 handles**: Livestock (kli) — regional only — **Module 73 handles**: Timber — special aggregation

**Reality in code**: every part of this is false in the default configuration.

- `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`
  (`modules/17_production/flexreg_apr16/equations.gms:10-11`). The equation domain is `k`.
- `k` = **crops + pasture + livestock + fish + wood + woodfuel**
  (`modules/14_yields/managementcalib_aug19/sets.gms:12-16`), and `kli(kap)` ⊂ `kap(k)`
  (`modules/16_demand/sector_may15/sets.gms:16,21`). So `vm_prod_reg(i,livst_rum)` **is** the
  cell sum of `vm_prod(j,livst_rum)` — exactly the assignment the doc labels an ERROR.
- Cell-level livestock production is a first-class, **default-active** mechanism:
  `cfg$gms$disagg_lvst <- "foragebased_jul23"` (`config/default.cfg:2221`) and that realization
  constrains `vm_prod(j2,kli_rum)` and `vm_prod(j2,kli_mon)` directly
  (`modules/71_disagg_lvst/foragebased_jul23/equations.gms:23,55-57`).
- Timber is **not** "special aggregation": `modules/73_timber/default/equations.gms:43-50`
  populates `vm_prod(j2,"wood")` / `vm_prod(j2,"woodfuel")`, and since `wood, woodfuel ∈ k`,
  `q17_prod_reg` aggregates them like everything else.
- (`"beef"` is also not a set member; the commodity is `livst_rum`.)

**Why Critical**: a developer extending Module 17 / 71 who acts on this builds on a false model
structure — the doc tells them the cell→region livestock pathway does not exist when it is the
default-active pathway. Matches the Critical trigger *"Claimed a function/variable/file does not
exist when it does"* applied to a mechanism. (A Major reading is defensible under the tie-breaker;
recorded here as Critical because the negative is categorical and about the DEFAULT config.)

**verify_cmd**:
```
sed -n '10,11p' modules/17_production/flexreg_apr16/equations.gms
# -> q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
sed -n '12,16p' modules/14_yields/managementcalib_aug19/sets.gms
# -> k(kall) Primary products / ... livst_rum, livst_pig, livst_chick, livst_egg, livst_milk, fish, wood, woodfuel/
sed -n '16,22p' modules/16_demand/sector_may15/sets.gms   # -> kap(k) ... ; kli(kap) ...
grep -n 'disagg_lvst' config/default.cfg                  # -> 2221: cfg$gms$disagg_lvst <- "foragebased_jul23"
sed -n '55,57p' modules/71_disagg_lvst/foragebased_jul23/equations.gms  # -> vm_prod(j2,kli_mon) =l= ...
```

**Fix**: replace the whole MISTAKE-1 block. `vm_prod_reg` is declared over `kall`;
`q17_prod_reg` covers `k` (crops, pasture, **livestock**, fish, wood, woodfuel) — the residue
(`kres`) and secondary-product (`ksd`) slices of `vm_prod_reg` are instead set by `18_residues`
and `20_processing`. The real MISTAKE-1 to warn about is the multi-populator structure of
`vm_prod_reg` (17 / 18 / 20 / 21 all write slices of it), not a plant-only scope.

---

## BUG-02 — Major — `formula`

**doc**: `modification_safety_guide:827` (§6.1 Error Pattern 1, Fix step 2)

> 2. Verify transition matrix: `sum(land_from, vm_lu_transitions) = pcm_land`

**Reality in code**: the index is inverted. `modules/10_land/landmatrix_dec18/equations.gms:19-25`:

```
q10_transition_to(j2,land_to)  .. sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e= vm_land(j2,land_to);
q10_transition_from(j2,land_from) .. sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);
```

Summing over `land_from` gives **`vm_land`**, not `pcm_land`. The doc's own §1.4 (lines 109-110)
states this correctly, so §6.1 also contradicts the same document.

**verify_cmd**: `sed -n '19,25p' modules/10_land/landmatrix_dec18/equations.gms` → as quoted.

**Fix**: `sum(land_to, vm_lu_transitions(j,land_from,land_to)) = pcm_land(j,land_from)` **and**
`sum(land_from, vm_lu_transitions(j,land_from,land_to)) = vm_land(j,land_to)`.

---

## BUG-03 — Major — `formula`

**doc**: `modification_safety_guide:148` (§1.5 test 2, block 146-153)

> `# Verify row sums = column sums` … `stopifnot(all(abs(row_sums - col_sums) < 1e-6))`
> with `row_sums <- dimSums(transitions, dim="to")`, `col_sums <- dimSums(transitions, dim="from")`

**Reality in code**: the two are not element-wise equal and the test would fail on any run with
land-use change. Per `equations.gms:19-25`, summing over `to` yields `pcm_land` indexed by
`land_from`; summing over `from` yields `vm_land` indexed by `land_to`. They coincide only after
a further sum over all land types (that aggregate identity is `q10_land_area`, `equations.gms:13-15`).

**verify_cmd**: `sed -n '13,25p' modules/10_land/landmatrix_dec18/equations.gms` → row sum = `pcm_land`,
column sum = `vm_land`; equality only under `sum(land, ...)`.

**Fix**: test the two invariants separately (`dimSums(transitions, dim="to") == pcm_land` and
`dimSums(transitions, dim="from") == vm_land`), or, if only one check is wanted, compare the
**totals**: `dimSums(transitions, dim=c("from","to"))` constant across time steps.

---

## BUG-04 — Major — `set_membership`

**doc**: `modification_safety_guide:174` (§1.6, inside a block headed **✅ SAFE**)

> `vm_lu_transitions.fx(j,"forest","crop")$(pm_land_conservation(j,"forest") > 0) = 0;`

**Reality in code**: two independent domain errors in a snippet labelled SAFE.

1. `"forest"` is not a member of `land`. `core/sets.gms:250-251`:
   `land Land pools / crop, past, forestry, primforest, secdforest, urban, other /`.
2. `pm_land_conservation` is declared with **four** indices —
   `pm_land_conservation(t,j,land,consv_type)`
   (`modules/22_land_conservation/area_based_apr22/declarations.gms:15`) — the snippet passes two.

As written this is a GAMS domain violation, not a safe modification.

**verify_cmd**:
```
sed -n '250,251p' core/sets.gms
grep -n 'pm_land_conservation' modules/22_land_conservation/area_based_apr22/declarations.gms
```

**Fix**: e.g.
`vm_lu_transitions.fx(j,"primforest","crop")$(sum(ct, pm_land_conservation(ct,j,"primforest","protect")) > 0) = 0;`
(and verify the intended `consv_type` member against `modules/22_land_conservation/area_based_apr22/sets.gms`).

---

## BUG-05 — Major — `mechanism`

**doc**: `modification_safety_guide:180` (§1.6, **✅ SAFE**, captioned *"Higher cost for primary forest conversion"*)

> `vm_cost_landcon.up(j,"primforest") = 1e6;  * USD/ha`

**Reality in code**: `.up` sets an **upper bound** on a variable that is pinned by an equality:

```
q39_cost_landcon(j2,land) .. vm_cost_landcon(j2,land) =e= (…)   # modules/39_landconversion/calib/equations.gms:12-15
```

An upper bound cannot raise a cost. At 1e6 it is simply non-binding; set below the equality value
it makes the model infeasible. The unit annotation is also wrong: `vm_cost_landcon(j,land)` is in
**mio. USD17MER per yr** (`modules/39_landconversion/calib/declarations.gms:13`), not USD/ha.

**verify_cmd**:
```
sed -n '12,15p' modules/39_landconversion/calib/equations.gms   # -> =e=
grep -n 'vm_cost_landcon' modules/39_landconversion/calib/declarations.gms
# -> vm_cost_landcon(j,land)  Costs for land expansion and reduction (mio. USD17MER per yr)
```

**Fix**: raise the driver, not the bound — `i39_cost_establish(t,i,"primforest")` in
`modules/39_landconversion/calib/`. Also drop or correct the `* USD/ha` comment. (Separately: the
section heading claims the change "affects Module 29, 30, 32, 35"; `vm_cost_landcon` is read only
by `11_costs` — see the deferred list.)

---

## BUG-06 — Major — `set_membership`

**doc**: `modification_safety_guide:482` (§4.3 switch table)

> `c56_emis_policy` | reddnatveg_nosoil | **60+ policies** | Which emissions priced

**Reality in code**: the closed set `scen56` has **44** members
(`modules/56_ghg_policy/price_aug22/sets.gms:119-163`) and it is the domain of
`f56_emis_policy(scen56,pollutants_all,emis_source)`, so 44 is the exhaustive option count.
`modules/module_56.md:36` already says "44 policies" — this doc is also out of step with its sibling.

**verify_cmd**: parse the `scen56 / … /` block of
`modules/56_ghg_policy/price_aug22/sets.gms` → 44 members
(`none, all, all_nosoil, …, co2_reddnatveg_nosoil_peatland`).

**Fix**: change "60+ policies" to "44 policies (set `scen56`,
`modules/56_ghg_policy/price_aug22/sets.gms:119-163`)".

---

## BUG-07 — Major — `formula` (units)

**doc**: `modification_safety_guide:514` (§4.5 MISTAKE 1) and `:886` (§6.1 Error Pattern 4, Fix step 1)

> `im_pollutant_prices(t,i,"co2_c","all") = 10000;  * 10,000 USD/tCO2!`
> … 1. Check `im_pollutant_prices`: should be 0-500 USD/tCO2

**Reality in code**: the `co2_c` slice of `im_pollutant_prices` is in **USD17MER per t C**, not per
t CO2 — a factor of 44/12 = 3.67.

- `im_pollutant_prices(t_all,i,pollutants,emis_source) … (USD17MER per Mg)`
  (`modules/56_ghg_policy/price_aug22/declarations.gms:9`)
- `s56_minimum_cprice  Minium C price (USD17MER per tC) / 3.67 /` (`input.gms:67`) is applied
  directly to the `co2_c` slice at `preloop.gms:74`.
- `preloop.gms:77`: `*12/44 conversion from USD17MER per tC to USD17MER per tCO2`.

So `10000` is 2 727 USD/tCO2 (not 10 000), and the "0-500 USD/tCO2" acceptance band corresponds to
0-1 835 in the parameter's own units. A user applying the doc's check would flag legitimate
high-ambition scenarios as errors.

Same unit slip (less load-bearing, context is the scenario's native reporting unit) at `:481`
"0-1000+ USD/tCO2" and `:520` "Typical range: 0-500 USD/tCO2 by 2100".

**verify_cmd**:
```
grep -n 'im_pollutant_prices' modules/56_ghg_policy/price_aug22/declarations.gms
grep -n 's56_minimum_cprice' modules/56_ghg_policy/price_aug22/input.gms   # -> 67: (USD17MER per tC) / 3.67 /
sed -n '74,78p' modules/56_ghg_policy/price_aug22/preloop.gms              # -> 77: *12/44 conversion from USD17MER per tC to USD17MER per tCO2
```

**Fix**: state the parameter's unit once ("USD17MER per t C for `co2_c`") and convert the
thresholds: "0-500 USD/tCO2 ⇒ 0-1835 in `im_pollutant_prices` units (×44/12)".

---

## BUG-08 — Major — `citation`

**doc**: `modification_safety_guide:609` (§5.1)

> **Critical Feedback Cycles** (from Module_Dependencies.md:151-179)

**Reality**: `core_docs/Module_Dependencies.md:151-179` is the Layer-4/5/6 architecture block plus
`#### 3.2 Hub-and-Spoke Patterns`. The content actually quoted lives at
`### 4. Circular Dependencies (Feedback Loops)` / `#### 4.1 Critical Feedback Cycles`,
**lines 182-216**. The cited range ends 3 lines before the section it claims to quote.

**verify_cmd**:
```
grep -n '#### 3.2 Hub-and-Spoke\|### 4. Circular\|#### 4.1 Critical Feedback' core_docs/Module_Dependencies.md
# -> 166, 182, 184
```

**Fix**: cite `core_docs/Module_Dependencies.md § 4.1 Critical Feedback Cycles` (section anchor, per
the precedent already set in this doc's Appendix A note).

---

## BUG-09 — Major — `data_flow_direction`

**doc**: `modification_safety_guide:496-497` (§4.4 interaction diagram)

> `├─ CDR Rewards → 32_forestry (afforestation incentive)`
> `│     └─ Affects land competition (forest vs. crop)`

**Reality in code**: the data flow runs the other way. `vm_cdr_aff(j,ac,aff_effect)` is **declared
in 32_forestry** (`modules/32_forestry/dynamic_may24/declarations.gms:83` — the module's only
realization) and **read by 56** in `q56_reward_cdr_aff`
(`modules/56_ghg_policy/price_aug22/equations.gms:77`). Module 32 reads **no** module-56 interface
at all — a both-endpoints grep for `im_pollutant_prices|vm_emission_costs|vm_reward_cdr_aff|p56_`
across `modules/32_forestry/*/*.gms` returns nothing. The C-price signal reaches 32 only through
the shared objective (`vm_reward_cdr_aff` → `11_costs`, `equations.gms:27`), i.e. parallel/economic,
not a hand-off. The two sibling arrows in the same diagram *are* genuine data flows
(`vm_emission_costs` → 11, `im_pollutant_prices` → 57, the latter even carrying a file:line),
which is what makes the third one misleading.

Safety-relevant consequence: the guide omits the direction that actually matters here — a change to
32's `vm_cdr_aff` breaks 56, not the reverse.

**verify_cmd**:
```
grep -n 'vm_cdr_aff' modules/32_forestry/dynamic_may24/declarations.gms   # -> 83 (declared)
sed -n '73,78p' modules/56_ghg_policy/price_aug22/equations.gms           # -> 77: reads vm_cdr_aff
rg -Pn "(?<![A-Za-z0-9_])(im_pollutant_prices|vm_emission_costs|vm_reward_cdr_aff|p56_)" modules/32_forestry/*/*.gms
# -> no matches (positive control: `rg -c vm_ modules/32_forestry/dynamic_may24/equations.gms` is non-zero)
```

**Fix**: redraw as `32_forestry → vm_cdr_aff → 56_ghg_policy → vm_reward_cdr_aff → 11_costs
(objective) ⇒ afforestation incentive`, and label the 56→32 influence explicitly as
*economic, via the objective — no interface variable*.

---

## BUG-10 — Minor — `other`

**doc**: `modification_safety_guide:450` (§4.1)

> **Centrality**: HIGH

**Reality**: Appendix A of this same doc states the rule *"🔴 CRITICAL at `Reaches` ≥ 18, 🟠 HIGH at
≥ 12, 🟡 MEDIUM below"* (lines 1072-1074). The persisted tool measures `56_ghg_policy` at
**owns 5 / reaches 5 / depends_on 13**, i.e. 🟡 MEDIUM under the doc's own rule. (`17_production`
at reaches 12 → HIGH is consistent; `11_costs` "HIGHEST dependency count" is correct — 27 is the
maximum `depends_on` in the model.)

**verify_cmd**: `python3 audit/tools/compute_module_centrality.py --all | grep '^56,'`
→ `56,5,5,0,5,13`

**Fix**: either give 56 its measured numbers and a MEDIUM band with a sentence explaining why it is
still in this guide (it is the bridge into the objective function, so its *economic* blast radius
exceeds its interface reach), or state that its tier is assigned on economic influence rather than
on the `Reaches` rule.

---

## BUG-11 — Minor — `other`

**doc**: `modification_safety_guide:52` (and the identical recipe at `:1101`)

> Counts recomputed 2026-05-23 (R3) via
> `find ../modules -name '*.gms' -exec grep -l '<var>' {} \; | awk -F/ '{print $3}' | sort -u | grep -v '10_land'`

**Reality**: the documented recipe does **not** reproduce the (correct) documented numbers. A bare
substring `grep -l 'vm_land'` also matches `vm_landexpansion`, `vm_landreduction`, `vm_landdiff`,
so it returns **12** modules where the table correctly says **10** (it adds `39_landconversion` and
`80_optimization`). Same for the Appendix B note. A future maintainer re-running the printed command
would "correct" 10 → 12 and inject a real bug. (§3.2's note at `:338` uses `grep -l '\b<var>\b'` and
*is* correct — `_` is a word constituent, so `\bvm_prod\b` does not match `vm_prod_reg`.)

**verify_cmd**:
```
find modules -name '*.gms' -exec grep -l 'vm_land' {} \; | awk -F/ '{print $2}' | sort -u | grep -v '10_land' | wc -l
# -> 12   (adds 39_landconversion, 80_optimization)
rg -P -l "(?<![A-Za-z0-9_])vm_land(?![A-Za-z0-9_])" modules/*/*/*.gms | awk -F/ '{print $2}' | sort -u | grep -v '10_land' | wc -l
# -> 10   (matches the table)
```

**Fix**: replace both notes' recipe with the word-boundary form used at `:338`
(`grep -l '\b<var>\b'`) or the PCRE exact-token form, and add the caveat that macro-argument uses
(`m58_LandMerge(vm_land, …)`, `modules/58_peatland/v2/equations.gms:23`) have no trailing `(` or `.`
— which is why `58_peatland` is a real `vm_land` consumer that a `vm_land(`-only grep misses.

---

## BUG-12 — Minor — `set_membership`

**doc**: `modification_safety_guide:1095-1096` (Appendix B)

> `im_pop_iso(t,iso)` … `pm_interest(t,i)`

**Reality in code**: both are declared over `t_all`, not `t` —
`im_pop_iso(t_all,iso)` (`modules/09_drivers/aug17/declarations.gms:10`) and
`pm_interest(t_all,i)` (`modules/12_interest_rate/select_apr20/declarations.gms:9`).
`t ⊂ t_all` are distinct sets in MAgPIE. The same doc gets it right for
`im_pollutant_prices(t_all,…)` at `:464`, so this is an internal inconsistency.

**verify_cmd**:
```
grep -n 'im_pop_iso' modules/09_drivers/aug17/declarations.gms
grep -n 'pm_interest' modules/12_interest_rate/select_apr20/declarations.gms
```

**Fix**: `im_pop_iso(t_all,iso)`, `pm_interest(t_all,i)`.

---

## BUG-13 — Minor — `citation`

**doc**: `modification_safety_guide:477` (§4.3)

> **Configuration Switches** (modules/56_ghg_policy/price_aug22/input.gms:84-117)

**Reality in code**: three of the four tabled switches are at `input.gms:84-90`; the fourth,
`s56_c_price_induced_aff`, is at `input.gms:69` (inside the `scalars` block, 64-82) — outside the
cited range. Lines 91-117 are `f56_*` table declarations, not switches.

**verify_cmd**:
```
grep -n 'setglobal c56_\|s56_c_price_induced_aff' modules/56_ghg_policy/price_aug22/input.gms
# -> 69 (scalar), 84,85,86,87,88,90 ($setglobal)
```

**Fix**: cite `modules/56_ghg_policy/price_aug22/input.gms:64-90`.

---

## BUG-14 — Minor — `citation`

**doc**: `modification_safety_guide:1103` (Appendix B)

> **Source**: Module_Dependencies.md §2.1 (lines 46-59)

**Reality**: `#### 2.1 Most Connected Variables` is at `core_docs/Module_Dependencies.md:80`, its
table at 84-94. Lines 46-59 are §1.2 prose ("`11_costs` is deliberately not a row" / "Reading the
two columns"). The §2.1 anchor is right; only the line range drifted — which is exactly the failure
Appendix A already fixed for itself ("the previous 'lines 29-40' pointer had already drifted").

**verify_cmd**: `grep -n '#### 2.1 Most Connected' core_docs/Module_Dependencies.md` → `80`

**Fix**: drop the line range, cite `core_docs/Module_Dependencies.md § 2.1 Most Connected Variables`.

---

## BUG-15 — Minor — `citation`

**doc**: `modification_safety_guide:507` (§4.4)

> See: `cross_module/carbon_balance_conservation.md:450-550` for full carbon-policy interactions

**Reality**: lines 450-505 of that file are §6.1-6.3 (Chapman-Richards forest growth curves) and
508-550 are §7.1/§7.2 (Module 52 as data provider, Module 59 SOM). No carbon-**policy** interaction
content is inside the range; the closest is `### 7.4 Module 57 (MACCs) - Mitigation Costs` at line
587, outside it.

**verify_cmd**:
```
grep -n '^#\{2,4\} ' cross_module/carbon_balance_conservation.md | awk -F: '$1>380 && $1<620'
# -> 444 §6, 446 §6.1, 462 §6.2, 483 §6.3, 506 §7, 508 §7.1, 534 §7.2, 562 §7.3, 587 §7.4, 607 §7.5
```

**Fix**: cite `cross_module/carbon_balance_conservation.md § 7. Module Interactions for Carbon Balance`
(by section, no line range).

---

## BUG-16 — Minor — `data_flow_direction`

**doc**: `modification_safety_guide:613` (§5.1 cycle 1)

> `17_production ←→ 14_yields ←→ 70_livestock ←→ 17_production`

**Reality in code**: the `17 → 14` half of the first edge does not exist. Module 17 declares
exactly three interfaces — `vm_prod(j,k)`, `vm_prod_reg(i,kall)`, `pm_prod_init(j,kcr)`
(`modules/17_production/flexreg_apr16/declarations.gms:9,10,18`) — and **no file under
`modules/14_yields/` references any of them** (verified with two methods plus a positive control).
The real edge is `14 → 17` only (`pm_yields_semi_calib`, read at
`modules/17_production/flexreg_apr16/presolve.gms:10`); likewise `17 → 70` is one-way (70 reads
`vm_prod_reg`). The bidirectional arrows describe an economic feedback, not an interface cycle.
The claim is inherited verbatim from `core_docs/Module_Dependencies.md:190`, so a fix belongs in
both files.

**verify_cmd**:
```
rg -Pn "(?<![A-Za-z0-9_])(vm_prod|vm_prod_reg|pm_prod_init)(?![A-Za-z0-9_])" modules/14_yields/*/*.gms   # -> no matches
grep -rn 'vm_prod\|pm_prod_init' modules/14_yields/                                                      # -> no matches (2nd method)
rg -c 'vm_' modules/14_yields/managementcalib_aug19/equations.gms                                        # -> 3 (positive control: search works there)
```

**Fix**: mark the arrows that are interface edges vs. economic feedback, e.g.
`14_yields → 17_production (pm_yields_semi_calib) ; 17_production → 70_livestock (vm_prod_reg) ;
70 → 14 economic only`, or state up front that §5.1's cycles are behavioural, not data-flow.

---

## BUG-17 — Minor — `set_membership`

**doc**: `modification_safety_guide:514` and `:529` (§4.5 MISTAKE 1 and 2 code blocks)

> `im_pollutant_prices(t,i,"co2_c","all") = 10000;`

**Reality in code**: `"all"` is not a member of `emis_source`. The set is defined once, in
`core/sets.gms:302-312`, as `inorg_fert, man_crop, awms, resid, man_past, som, rice, ent_ferm,
resid_burn, crop_vegc … other_soilc, peatland` — no `all`, and no module extends it. The blocks are
labelled ❌ WRONG for a *different* reason (unrealistic magnitude), so a reader takes the addressing
pattern as correct.

**verify_cmd**:
```
sed -n '302,312p' core/sets.gms                                  # -> no "all"
rg -n 'emis_source\s*(Emission|/)' --glob '*.gms' .              # -> only core/sets.gms:302 (single definition)
rg -n '"all"' modules/56_ghg_policy/*/*.gms                      # -> no matches
rg -c '"co2_c"' modules/56_ghg_policy/price_aug22/preloop.gms    # -> 8 (positive control)
```

**Fix**: use a real member, e.g. `im_pollutant_prices(t,i,"co2_c",emis_source) = 10000;` or
`…,"primforest_vegc") = 10000;`.

---

## BUG-18 — Informational — `other`

**doc**: `modification_safety_guide:1041` (§8.3 Getting Help)

> 2. Search `` documentation

Empty inline code span — a reference whose target was removed. Not a content error; fix by naming
the corpus (e.g. "Search the `magpie-agent/modules/` and `core_docs/` documentation").

---

## Deferred (not verified / judgement calls — no edit proposed)

- **`vm_lu_transitions` described as "gross between-type transitions" (doc:47).** The matrix also
  carries diagonal (same-type persistence) entries — `q10_transition_from` sums over all `land_to`
  including `land_from` — so the parenthetical is compressed rather than plainly wrong. Only
  `vm_landexpansion`/`vm_landreduction` exclude the diagonal (`not sameas`). Left alone.
- **"✅ SAFE: Modifying transition costs (affects Module 29, 30, 32, 35)" (doc:177).**
  `vm_cost_landcon` is read only by `11_costs` (role map + exact-token grep), so as a data-flow
  claim it is wrong; as an economic-effect claim (which land types respond) it is defensible.
  Ambiguous phrasing, not flagged.
- **"Centrality: HIGHEST in entire model" for Module 10 (doc:34).** True on `Owns` (18, the model
  maximum) but the doc's own Appendix A ranks `31_past` first on `Reaches` (21 vs 18). The metric is
  unstated, so this is under-specified rather than false.
- **All `magpie4` R helpers used in the test snippets** (`land_transitions`, `water_avail`,
  `trade_balance`, `nr_inputs`, `nr_outputs`, `nr_soil_change`, `land_conservation`, `carbonstock`
  signatures) — not checkable from the GAMS worktree; belongs to the magpie4 lens.
- **§2.4 cost-magnitude thresholds** ("500-2000 billion" in the comment vs `< 5000` in the code, and
  whether `magpie4::costs` returns mio. or bn USD) — the internal comment/code mismatch is real but
  I cannot settle the unit without the pinned magpie4 source; not flagged.
- **`vm_prod_reg` multi-populator structure.** `17` (`q17_prod_reg`), `20`
  (`modules/20_processing/substitution_may21/equations.gms:41`) and `71`
  (`preloop.gms:17`, `.lo`) all write slices; the doc never makes an exclusive-producer claim strong
  enough to flag, but the §3.3 chain diagram shows Module 17 as the sole route. Folded into BUG-01's
  proposed fix rather than filed separately.
- **`config/default.cfg:1838` `c56_carbon_stock_pricing <- …` missing its `cfg$gms$` prefix.** An
  upstream MAgPIE oddity, not a defect of this doc; the effective default is still `actualNoAcEst`
  via `input.gms:90`.
