# M29 refutation pass (R58)

**Target**: `audit/archive/rounds/round58_hubs/module_29_audit.md` vs `../modules/29_cropland/` @ develop `0d7ebeb90`
**Date**: 2026-07-17
**Stance**: adversarial refuter. Each finding was attacked, not confirmed. A finding survives only where refutation failed against the `.gms` code.
**Discipline**: all ground truth read this session from `.gms` / `.csv` / `config`. No `scripts/check_*.py` consulted. Absence claims carry positive controls. `rg -n` only.

**Headline**: 18 of 19 findings survive intact; 1 (F2) is partially refuted and downgraded. Two of the auditor's *self-named classes* are refuted even where the finding stands (F4, F2). The two findings I attacked hardest — **F8** and **F13** — both got **stronger**: I closed the auditor's own acknowledged evidence gaps, and both closed against the doc.

---

### F1: `pm_carbon_density_soilc` phantom + fabricated Cycle C29 back-edge
- **verdict**: SURVIVES
- **my_independent_check**: pre-confirmed by the requester; not re-derived (per instructions).
- **reasoning**: Accepted as given. Consistent with my own reading of `29_cropland/detail_apr24/preloop.gms:1-68` — M29's inbound set contains nothing M59 declares.
- **severity_agreed**: Critical

---

### F2: `m_carbon_stock_ac` described as an additive sum over `ac` and `ac_sub`
- **verdict**: PARTIALLY_REFUTED
- **my_independent_check**: `core/macros.gms:104-106` (macro body, read in full); call site `modules/29_cropland/detail_apr24/equations.gms:42`; `stockType` set at `modules/56_ghg_policy/price_aug22/sets.gms:212-213`; doc text at `modules/module_29.md:181-183`.
- **reasoning**: The auditor's **code** claim is right — the macro is a mutually-exclusive `$(sameas(stockType,...))` dispatch, not an accumulation:
  ```gams
  $macro m_carbon_stock_ac(land,carbon_density,sets,sets_sub) \
     sum((&&sets), ...)$(sameas(stockType,"actual")) + \
     sum((&&sets_sub), ...)$(sameas(stockType,"actualNoAcEst"))
  ```
  But the auditor's **doc** claim overreads. The doc says verbatim: *"Sums carbon across age classes (ac) and subset (ac_sub)"*. That sentence does not assert addition and does not "invert control flow" — it is **silent** on control flow. It is literally compatible with the dispatch reading (the macro does contain a sum over `ac` and a sum over `ac_sub`). The defect is **omission of the dispatch**, not a misstatement of it. The auditor's `self_named_class` (`macro-expansion-misread-as-arithmetic`, "inverts its control flow") describes a defect the doc does not commit.
  Additionally, the reader-harm story the auditor prices at Major ("reader concludes `q29_carbon` double-counts") is driven by the **`stockType` gloss being wrong**, which is scored separately and correctly as **F3**. Scoring both at Major double-counts one reader harm through one root cause. F3 carries the falsifiable error ("reference" is not a set member); F2 carries only incompleteness.
- **if PARTIALLY**: **Stands** — the macro's dispatch semantics are undocumented, the natural reading of the bullet implies a single additive sum, and the doc never mentions `stockType` selection, so a reader cannot recover the `actualNoAcEst` purpose. **Does not stand** — "described as an additive sum" / "inverts its control flow" / `macro-expansion-misread-as-arithmetic`. The doc omits; it does not invert. Recommend merging F2 into F3 as the compounding half, or holding it at Minor.
- **severity_agreed**: **Minor** (down from Major)

---

### F3: `stockType` glossed as "Actual vs reference stocks"; no `reference` member exists
- **verdict**: SURVIVES
- **my_independent_check**: `modules/56_ghg_policy/price_aug22/sets.gms:212-213` read this session:
  ```gams
  stockType Carbon stock types
        / actual, actualNoAcEst /
  ```
  Doc text at `modules/module_29.md:186`: "**Stock Types** (stockType): Actual vs reference stocks".
- **reasoning**: Refutation attempted and failed. The set has exactly two members, `actual` and `actualNoAcEst`. There is no `reference` member, and the real axis (all age classes vs. excluding establishment age classes) is not an actual-vs-reference distinction. This is a flatly false claim about an exact set-member vocabulary, which the exact-set-member-labels MANDATE covers directly. The auditor's note that `sameas` against a non-member string silently yields an empty expression (a zero that looks like data) is correct GAMS behaviour and raises the harm above cosmetic.
- **severity_agreed**: Major

---

### F4: `simple_apr24` characterized as "simplified crop allocation without rotational constraints"
- **verdict**: SURVIVES (finding stands; **auditor's self-named class refuted**)
- **my_independent_check**: `modules/29_cropland/simple_apr24/equations.gms:12-13` (read in full — `q29_cropland(j2) .. vm_land(j2,"crop") =e= sum((kcr,w), vm_area(j2,kcr,w));`); `simple_apr24/realization.gms:8-12`; `rg -ni 'rotation' modules/29_cropland/` → **exit=1, zero matches**. **Positive control**: `rg -nic 'cropland' modules/29_cropland/simple_apr24/equations.gms` → **14 matches**, so the search path is live. Doc text at `modules/module_29.md:12`.
- **reasoning**: Both halves are false about M29, as claimed.
  1. `simple_apr24` performs no crop allocation — `q29_cropland` is a bare accounting identity against `vm_area`. Crop allocation is M30's job in both realizations.
  2. `rotation` appears nowhere in `modules/29_cropland/` in either realization (positive control confirms the search works).
  **But the auditor's diagnosis is wrong.** Their class `realization-contrast-confabulated-from-name` claims the contrast was "invented from the word 'simple'". It was not invented — it was **transplanted from Module 30**, which has *identically named* realizations (`detail_apr24` / `simple_apr24`). I read `modules/30_croparea/simple_apr24/realization.gms:8-10`: *"calculates the crop specific agricultural crop area endogenously based on yield data provided by module [14_yields] and **simplified rotational constraints**"* — and M30's `simple_apr24` genuinely does crop allocation with rotation equations (`modules/30_croparea/simple_apr24/equations.gms:34` `q30_rotation_max`, `:42` `q30_rotation_min`, `:66` `q30_crop_reg`). So the doc's sentence is a near-verbatim description of **M30's** realization contrast, misfiled under M29.
  This matters for the taxonomy: the generative mechanism is **cross-module transplant between identically-named realizations**, not name-based confabulation. That is a *more* dangerous and more checkable class (grep for realization names shared across modules), and it predicts where else to look. Note the transplant is wrong even as M30 prose: M30's `simple_apr24` has *simplified* rotational constraints, not *no* rotational constraints.
  The finding itself is untouched — the sentence sits in the top-of-doc default-realization callout and misinforms realization choice, while the real trade-off (`simple_apr24/preloop.gms:8-12` fixes `vm_cost_cropland`, `vm_fallow`, `vm_treecover`, and two `vm_bv` slices to zero) goes unstated.
- **severity_agreed**: Major (class should be renamed to something like `realization-contrast-transplanted-from-homonymous-module`)

---

### F5: "Fallow only used when target > 0" — real gate is `s29_fallow_max` = 0
- **verdict**: SURVIVES
- **my_independent_check**: pre-confirmed by the requester. Independently corroborated anyway while checking F13: `modules/29_cropland/detail_apr24/equations.gms:70-72` — `q29_fallow_max(j2) .. vm_fallow(j2) =l= vm_land(j2,"crop") * s29_fallow_max;` is **unguarded**; `equations.gms:66-68` — `q29_fallow_min(j2)$(sum(ct, i29_fallow_penalty(ct)) > 0)` is the penalty path; `equations.gms:28-33` — `v29_fallow_missing` enters `q29_cost_cropland`; `input.gms:33` `s29_fallow_max ... / 0 /`.
- **reasoning**: Confirmed. `s29_fallow_target > 0` activates the penalty branch without ever relaxing the `s29_fallow_max = 0` ceiling, so the run solves, produces zero fallow, and silently pays a penalty into the objective. The auditor's decision to hold at Major (because `:297` states the correct default two lines above) is defensible restraint under the "pick the lower tier when between" rule.
- **severity_agreed**: Major

---

### F6: `v29_treecover` presented as fully optimized; `ac_sub` is `.fx`'d
- **verdict**: SURVIVES
- **my_independent_check**: pre-confirmed by the requester (`presolve.gms:81`, `ac_est` free at `:79-80`).
- **reasoning**: Accepted as given. Independently consistent with `postsolve.gms:8` carry-forward and the `preloop.gms:36-38` initialization I read for F13.
- **severity_agreed**: Major

---

### F7: `s29_treecover_bii_coeff` inert for years ≤ `sm_fix_SSP2`; doc omits the guard
- **verdict**: SURVIVES
- **my_independent_check**: `modules/29_cropland/detail_apr24/presolve.gms:44-52`, read this session:
  ```gams
  if(m_year(t) <= sm_fix_SSP2,
   p29_treecover_bii_coeff(bii_class_secd,potnatveg) = fm_bii_coeff(bii_class_secd,potnatveg)
  else
   if(s29_treecover_bii_coeff = 0, ...
   elseif s29_treecover_bii_coeff = 1, ... = fm_bii_coeff("timber",potnatveg) );
  );
  ```
  `config/default.cfg:225` → `cfg$gms$sm_fix_SSP2 <- 2025`.
- **reasoning**: Refutation attempted and failed. The guard is real, the doc (`module_29.md:404-409`) presents the switch unconditionally, and the threshold lives in a different module's config key. The switch is genuinely a no-op for every timestep ≤ 2025 regardless of its value. Not severity inflation: the harm (user sets the switch, sees no 2020/2025 BII difference, concludes it is broken) is concrete.
  Minor caveat on the auditor's framing: under defaults this switch is *doubly* inert, because tree cover is 0 anyway (F13), so `p29_treecover_bii_coeff` multiplies zero area. That makes F7 a live concern only in configs where tree cover is switched on — which slightly narrows its blast radius but does not make the omission correct. Major holds.
- **severity_agreed**: Major

---

### F8: Plantation curve claimed to converge to a *lower* final carbon density
- **verdict**: SURVIVES — **and is materially stronger than the auditor claimed**
- **my_independent_check**: I closed the exact gap the auditor flagged. Read this session:
  - `core/macros.gms:18` — `$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m;`
  - `core/macros.gms:20` — `$macro m_growth_litc_soilc(start,end,ac) (start + (end - start) * 1/20 * ac*5)$(ac <= 20/5) + end$(ac > 20/5);`
  - `modules/52_carbon/normal_dec17/start.gms:17` (plantation vegc), `:20` (plantation litc), `:27` (secdforest vegc), `:30` (secdforest litc), `:43-44` (`_uncalib` snapshots taken **before** calibration).
  - `modules/52_carbon/input/f52_growth_par.csv` — all 128 rows read.
  - Doc text at `modules/module_29.md:653-656`.
- **reasoning**: The auditor rated this medium-high because they verified only the code *comment*, not the arrays, and honestly conceded: *"If the plantation array in fact plateaus lower, the doc's claim would be accidentally true."* **It cannot.** I attacked exactly that possibility and it is structurally foreclosed:

  1. **The asymptote is the same symbol in both assignments.** Both curves pass `fm_carbon_density(t_all,j,"secdforest","vegc")` as the `A` argument:
     - plantation: `m_growth_vegc(pc52_carbon_density_start(...,"vegc"), fm_carbon_density(t_all,j,"secdforest","vegc"), f52_growth_par(clcl,"k","plantations"), f52_growth_par(clcl,"m","plantations"), ord(ac)-1)`
     - secdforest: `m_growth_vegc(pc52_carbon_density_start(...,"vegc"), fm_carbon_density(t_all,j,"secdforest","vegc"), f52_growth_par(clcl,"k","natveg"), f52_growth_par(clcl,"m","natveg"), ord(ac)-1)`
     Identical `S`, identical `A`. Only `k` and `m` differ. Since `(1-exp(-k·5·ac))^m → 1` as `ac → ∞` for any finite `k,m > 0`, both converge to **exactly `A`**. There is no "plantation carbon density" asymptote in the model — the phrase names a quantity that does not exist.
  2. **The `litc` pool is bit-identical.** The two `litc` assignments are the *same expression*, character for character (same `start`, same `end`, no `k`/`m`). Plantation litc ≡ secdforest litc at every age class.
  3. **The `vegc` inequality runs the opposite way to the doc.** With `x = 1-exp(-k·5·ac) ∈ (0,1)` and value `= A·x^m` (since `S = 0` for vegc, `start.gms:9`), higher `k` ⇒ higher `x`, and lower `m` ⇒ higher `x^m`. From `f52_growth_par.csv`, plantations have **strictly higher `k` in every climate class where the two differ** (e.g. Cfa: 0.042 vs 0.0219; Af: 0.0301 vs 0.0228; Dfa: 0.0257 vs 0.0198; equal at 0.01 only in BSh/BSk/BWh/BWk/EF/ET), and mostly **lower `m`** (Cfa: 3.37 vs 3.7991; Af: 1.69 vs 3.28). The one class where plantation `m` is marginally higher (Dfa: 4.64 vs 4.6112) is dominated by the `k` gap — I evaluated it at both ends: at `ac=1` plantation = 5.44e-5·A vs natveg = 1.85e-5·A; at `ac=60` plantation = 0.9979·A vs natveg = 0.9879·A. Plantation is higher at both.

  **Conclusion**: `pm_carbon_density_plantation_ac_uncalib ≥ pm_carbon_density_secdforest_ac_uncalib` at every age class, for both `ag_pools`, converging to equality — never below. The doc's *"Converges to plantation carbon density (typically lower than natural)"* and *"**Trade-off**: Plantation grows faster initially but has lower final carbon density"* are not merely unsupported by M29 — they are **inverted** relative to the arrays the model actually uses. The auditor's residual is resolved against the doc, and their confidence should go **medium-high → high**.

  The auditor's class name (`domain-plausible-tradeoff-overwriting-code-comment`) is accurate and now stronger: the doc imported a real-world ecological trade-off that the model does not implement, over an authoring comment (`preloop.gms:42-44`) that denies it. I confirmed that comment is present and that commit `75d7ee167` (2026-03-15) left it intact while renaming the parameters beneath it.
- **severity_agreed**: Major. (Arguably Critical — it is a fabricated causal mechanism that inverts the sign of a long-run carbon result under a carbon price, i.e. the "MAgPIE accounts for X" hazard in its inverted form. I hold at Major only because the "pick the lower tier when between" rule applies and `s29_treecover_plantation` is off by default.)

---

### F9: "Provides To" set wrong — two interfaces omitted, two descriptions fabricated
- **verdict**: SURVIVES
- **my_independent_check**: all four sub-claims re-derived independently:
  1. `rg -n 'pm_avl_cropland_iso[(.]' modules/ | grep -v 29_cropland` → **7 hits in 5 realizations across 3 modules**: `modules/13_tc/endo_jan22/presolve.gms:49,59`; `modules/13_tc/exo/presolve.gms:25,35`; `modules/30_croparea/detail_apr24/preloop.gms:41`; `modules/30_croparea/simple_apr24/preloop.gms:25`; `modules/59_som/cellpool_jan23/preloop.gms:110`. M29 is sole producer: declared `modules/29_cropland/detail_apr24/declarations.gms:20`, populated `detail_apr24/preloop.gms:58` and `simple_apr24/preloop.gms:35`. (Auditor said "four realizations"; it is **five** — an undercount in the safe direction.)
  2. `vm_carbon_stock` written by `q29_carbon` at `detail_apr24/equations.gms:38-42` (read this session); the Provided table at `module_29.md:681-684` lists only `vm_cost_cropland`, `vm_fallow`, `vm_treecover`, `vm_bv` — `vm_carbon_stock` is absent, while `:892` names M52 in the prose list. The table and the list disagree.
  3. "Module 59 — Soil organic matter targets for cropland" (`:893`): `v59_som_target` is computed **inside M59** — `modules/59_som/cellpool_jan23/equations.gms:20-21` (`q59_som_target_cropland`), `:31-32`, `:48`. M29 supplies M59 with `vm_fallow` / `vm_treecover` (`59_som/cellpool_jan23/equations.gms:25-26`) and `pm_avl_cropland_iso` (`preloop.gms:110`). Not SOM targets. Fabricated.
  4. "Module 22 — Protected cropland area (if applicable)" (`:894`): M22 reads `vm_treecover.l` at `modules/22_land_conservation/area_based_apr22/presolve_ini.gms:87,98,109`. "Protected cropland area" flows the other way via `pm_land_conservation`, which the doc itself lists correctly as an **inbound** at `:697`. Fabricated, arrow reversed.
- **reasoning**: Refutation attempted on every sub-claim and failed on every one. The doc names 5 modules and hedges "1-2 other"; M13 and M30 — both real consumers via `pm_avl_cropland_iso`, gated by the same `%c29_marginal_land%` switch the doc documents — appear nowhere in the downstream set. The auditor's point that the hedge is *engineered to be unfalsifiable* is fair and the numeric gap is larger than the hedge admits.
  One correction to the auditor: their `code_evidence` cites `simple_apr24/preloop.gms:35`(=preloop tail line 28)` — the parenthetical is noise; the line is simply 35, which I read. Does not affect the finding.
- **severity_agreed**: Critical (wrong producer/consumer set, per stated precedent)

---

### F10: M10 land balance quoted with `pm_land_start(j)`; actual closes against `pcm_land`
- **verdict**: SURVIVES
- **my_independent_check**: `modules/10_land/landmatrix_dec18/equations.gms:13-15`, read this session:
  ```gams
   q10_land_area(j2) ..
    sum(land, vm_land(j2,land)) =e=
    sum(land, pcm_land(j2,land));
  ```
  `modules/10_land/landmatrix_dec18/declarations.gms:9` → `pm_land_start(j,land)` — **two** indices. Doc at `module_29.md:932`, `:951`, `:985`.
- **reasoning**: Confirmed on both counts: wrong anchor parameter (`pm_land_start` vs `pcm_land`) and a malformed reference (`pm_land_start(j)` drops the `land` index and the outer `sum`). The auditor's *nuance* paragraph — conceding that the doc's check is numerically true though wrongly attributed and malformed, because `q10_land_area` conserves the per-cell total each step and `pcm_land` is seeded from `pm_land_start` — is exactly the kind of self-restraint that makes the rest credible, and I could not improve on it. The defect that remains is real: the expression as written is a domain error, and it is prescribed three times, twice inside "✅ Verify:" checklist items.
- **severity_agreed**: Major

---

### F11: "Total Connections: 12 (6/6)" vs cited source's 13 (6/7); section pointer wrong
- **verdict**: SURVIVES
- **my_independent_check**: `magpie-agent/core_docs/Module_Dependencies.md:39` read this session → `| 9 | **29_cropland** | 13 | 6 | 7 | Cropland management |` under header `| Rank | Module | Total | Provides To | Depends On |`. Section headings: `#### 1.2 Module Centrality Rankings` at **line 25**; `#### 3.1` at **line 89** is **"Architectural Layers"** — not a centrality table. Doc at `module_29.md:885-886`, `:907`.
- **reasoning**: Refutation attempted and failed on both halves. The cited source says 13 / 6 / 7; the doc says 12 / 6 / 6. Only "Rank 9" matches. The `§3.1` pointer resolves to a different section entirely. The auditor's third point — that both numbers understate reality given F9's ~11-module outward degree — is a fair independent observation and I verified its premise under F9.
- **severity_agreed**: Major

---

### F12: Downstream section assigns `vm_fallow` / `vm_treecover` to Module 44
- **verdict**: SURVIVES
- **my_independent_check**: exhaustive grep in both paren- and dot-form, run this session:
  - `rg -n 'vm_fallow[(.]' modules/ | grep -v 29_cropland` → `59_som/static_jan19/equations.gms:13`; `59_som/cellpool_jan23/equations.gms:25`; `50_nr_soil_budget/macceff_aug22/equations.gms:26`; `32_forestry/dynamic_may24/presolve.gms:18` → **{32, 50, 59}**.
  - `rg -n 'vm_treecover[(.]' modules/ | grep -v 29_cropland` → `22_land_conservation/area_based_apr22/presolve_ini.gms:87,98,109`; `59_som/cellpool_jan23/equations.gms:26`; `59_som/static_jan19/equations.gms:14` → **{22, 59}**.
  - `rg -n 'vm_fallow|vm_treecover' modules/44_biodiversity/` → **exit=1, zero matches**. **Positive control**: the same two patterns returned hits in `modules/59_som/` and `modules/32_forestry/` above, so the pattern and path are live.
  - `vm_bv(j,landcover44,potnatveg)` declared in `modules/44_biodiversity/bv_btc_mar21/declarations.gms:19`.
- **reasoning**: Confirmed. The doc's own table at `:682-683` is correct and its downstream list at `:811-812` is wrong; M44 touches M29 only through the pre-multiplied `vm_bv` slices. The auditor's observation that this is detectable **without reading any code** — purely by cross-reading two sections of one file — is correct and is the most efficient lens finding in the round.
- **severity_agreed**: Major

---

### F13: Doc never states fallow and tree cover are both identically zero under `config/default.cfg`
- **verdict**: SURVIVES — **and my refutation attempt closed the auditor's own acknowledged gap against the doc**
- **my_independent_check**: I attacked the tree-cover dominance argument, which the auditor explicitly flagged as reasoning rather than measurement (*"I did not exhaustively rule out an external incentive reaching `v29_treecover` through `vm_treecover` → M22/M59"*). Read this session:
  - `modules/29_cropland/detail_apr24/input.gms:12-13,24,33,35` — `s29_snv_shr / 0 /`, `s29_snv_shr_noselect / 0 /`, `s29_treecover_target / 0 /`, `s29_fallow_max / 0 /`, `s29_treecover_map / 0 /`. All confirmed.
  - `detail_apr24/equations.gms:28-33` (`q29_cost_cropland`), `:66-72` (`q29_fallow_min` / `q29_fallow_max`), `:38-42` (`q29_carbon`).
  - `detail_apr24/preloop.gms:37-38` — `elseif s29_treecover_map = 0, pc29_treecover(j,ac) = 0`.
  - **The channel I went after**: `config/default.cfg:1731` → `cfg$gms$c56_pollutant_prices <- "R34M410-SSP2-NPi2025"` — a **non-zero** carbon price by default. If cropland above-ground carbon were priced, planting tree cover would earn a carbon reward through `q29_carbon → vm_carbon_stock(j,"crop",...) → M56`, and the dominance argument would collapse.
  - **It is not priced.** `config/default.cfg:1828` → `cfg$gms$c56_emis_policy <- "reddnatveg_nosoil"`. I parsed `modules/56_ghg_policy/input/f56_emis_policy.csv` row `reddnatveg_nosoil,co2_c` against its header and the priced columns are exactly: `primforest_vegc`, `primforest_litc`, `secdforest_vegc`, `secdforest_litc`, `other_vegc`, `other_litc`, `peatland`. The crop columns are **`crop_vegc = 0`, `crop_litc = 0`, `crop_soilc = 0`**, and `som = 0`.
- **reasoning**: My refutation **failed, and in failing it strengthened the finding**. The most plausible external incentive — the default carbon price reaching cropland tree carbon — is explicitly zeroed for `crop_vegc`/`crop_litc` under the default emission policy, and the SOM route is zeroed too (`som = 0`, hence "nosoil"). So under `config/default.cfg`: planting tree cover on cropland earns **no** carbon revenue, costs `s29_cost_treecover_est = 2460` USD17MER/ha annuitized plus `s29_cost_treecover_recur = 615` USD17MER/ha/yr, consumes scarce cropland via `q29_cropland`, and avoids no penalty (`s29_treecover_target = 0` ⇒ `q29_treecover_min` yields `v29_treecover_missing =g= 0`). It is strictly dominated. The residual M22 channel is a `.l` read in `presolve_ini` — a previous-solve level, not an in-solve optimization channel — so it cannot incentivize planting in a recursive-dynamic solve. **The auditor's dominance argument holds, and the gap they flagged is now closed.**
  The behavioural-equivalence claim also checks out: with fallow ≡ 0 and tree cover ≡ 0, `q29_cost_cropland` (`equations.gms:28-33`) has every term zero ⇒ `vm_cost_cropland = 0` (= `simple_apr24/preloop.gms:8`'s `.fx`); both `vm_bv` slices evaluate to 0 (= simple's `.fx`); `q29_carbon` collapses to `vm_carbon_stock = vm_carbon_stock_croparea` (= `simple_apr24/equations.gms:29-31`); `q29_cropland` collapses to `simple_apr24/equations.gms:12-13`. So `detail_apr24` really is numerically `simple_apr24` at defaults.
  On whether this is severity inflation: it is not. AGENT.md carries an explicit **capability-vs-default MANDATE**, and F13 is squarely it — the doc's "Key Innovation" (`:21`) advertises machinery that is off out of the box. The auditor's restraint in holding at Major (because the individual defaults *are* stated correctly at `:735-736`, `:746`, `:766-767`) is correct.
- **severity_agreed**: Major

---

### F14: Doc certifies itself defect-free — "Zero discrepancies", "100% verified", "80+ citations"
- **verdict**: SURVIVES
- **my_independent_check**: `modules/module_29.md:3`, `:1090-1097`, `:1103-1104` read this session — verbatim: "**No Errors Found**: Zero discrepancies between code and documentation", "**Verification Status**: 100% verified", "**Citation Density**: 80+ file:line citations".
  Citation count, measured this session: `rg -o '[A-Za-z0-9_/.-]+\.(gms|cfg|md|R|csv|cs3|cs2):[0-9]+' modules/module_29.md | wc -l` → **59** (54 unique) across *all* file types, not 80+. And `rg -n '\`equations\.gms\`' modules/module_29.md | wc -l` → **28** bare citations with no line number (e.g. `:229`, `:238`, `:258`, `:267`, `:287`).
- **reasoning**: Refutation attempted and failed. These are falsifiable claims *in the documentation*, and they are false:
  - "Zero discrepancies" / "100% verified" — refuted by the 18 surviving findings, 2 of them Critical.
  - "80+ file:line citations" — **59** by direct count, generous regex. Inflated ~35%.
  The auditor's own concession that "**All 16 equation formulas match source code exactly**" is **true** is important and correct — it is the scope creep from that true narrow claim to the false total claim that constitutes the defect, and the auditor names this precisely.
  I considered refuting on the grounds that this is a claim *about the document* rather than about MAgPIE, and therefore out of scope. I reject that: a false, checkable assertion printed in the doc is a doc defect regardless of its subject, and this one measurably suppresses the scepticism that would surface the others.
- **severity_agreed**: Major

---

### F15: "Changes Since Last Verification: None (stable)" — five files changed; footer self-refuting
- **verdict**: SURVIVES
- **my_independent_check**: `git log --since=2025-10-13 --oneline --name-only -- modules/29_cropland/` run this session → **4 commits**: `896a9b728` (2026-03-21), `4f4107f2b`, `75d7ee167` → `detail_apr24/preloop.gms` + `simple_apr24/not_used.txt`, `16fb719e4` → `detail_apr24/realization.gms`, `da316ed4a` → `detail_apr24/scaling.gms`. `git log -1 --format='%ai' -- modules/29_cropland/` → **2026-03-21**. Doc footer at `module_29.md:1108-1111`.
  **The self-refutation, verified directly**: `git show 75d7ee167 -- modules/29_cropland/detail_apr24/preloop.gms` (dated **2026-03-15 22:42:14 +0100**) shows the rename `pm_carbon_density_secdforest_ac` → `pm_carbon_density_secdforest_ac_uncalib` (2 insertions, 2 deletions). The doc uses the **`_uncalib`** names at `:642`, `:650`, `:902` — i.e. the body reflects post-2026-03-15 code. And `git log --diff-filter=A -- modules/29_cropland/detail_apr24/scaling.gms` → created in `da316ed4a`, so the file did not exist on 2025-10-13, yet the doc's Scaling section (`:776-780`) describes it.
- **reasoning**: Refutation attempted and failed. Both of the auditor's independent proofs check out against git directly. The footer claims a verification date of 2025-10-13 and asserts nothing changed since, while the body demonstrably describes code that did not exist until 2026-03-15. The auditor's sharpest point survives too: because the footer is wrong *in the direction of reassurance*, it cannot even be trusted as a lower bound — this is qualitatively worse than ordinary footer staleness, so separating `metadata-footer-decoupled-from-body` from the Minor "stale footer" class is justified.
- **severity_agreed**: Major

---

### F16: `p29_avl_cropland` cited at `presolve.gms:32`; it is at `:35`
- **verdict**: SURVIVES
- **my_independent_check**: `modules/29_cropland/detail_apr24/presolve.gms:30-36` read this session. Line **32** = `p29_snv_relocation(t,j)$(p29_snv_relocation(t, j) > p29_max_snv_relocation(t,j)) = p29_max_snv_relocation(t,j);`. Line **35** = `p29_avl_cropland(t,j) = f29_avl_cropland(j,"%c29_marginal_land%") * (1 - p29_snv_shr(t,j));`. Doc at `module_29.md:117`.
- **reasoning**: Confirmed. Trivially true but real, and the auditor already priced it correctly as Minor precisely because the quoted code is right. No inflation.
- **severity_agreed**: Minor

---

### F17: `f29_snv_target_cropland` dims given as `(j, relocation_target)`; set is `relocation_target29`
- **verdict**: SURVIVES
- **my_independent_check**: `modules/29_cropland/detail_apr24/sets.gms:13-14` read this session → `relocation_target29 Cropland requiring relocation based on different SNV targets / SNV20TargetCropland, SNV50TargetCropland /`. Doc at `module_29.md:668`.
- **reasoning**: Confirmed. Bare `relocation_target` is not a set. The auditor's observation that the doc gets the sibling `marginal_land29` right two rows above (`sets.gms:10-11` confirms that set exists) makes this an inconsistency within one table rather than a systematic convention error. Minor is the right tier.
- **severity_agreed**: Minor

---

### F18: Table cites `declarations.gms:38-45` as source for a `vm_bv` row M29 does not declare
- **verdict**: SURVIVES
- **my_independent_check**: `modules/29_cropland/detail_apr24/declarations.gms:36-46` read in full this session — the positive-variables block contains exactly `vm_cost_cropland`(38), `vm_treecover`(39), `v29_treecover`(40), `v29_treecover_missing`(41), `v29_cost_treecover_est`(42), `v29_cost_treecover_recur`(43), `vm_fallow`(44), `v29_fallow_missing`(45). `rg -n 'vm_bv' modules/29_cropland/detail_apr24/declarations.gms` → **exit=1, zero matches**. **Positive control**: `rg -n 'vm_fallow' <same file>` → returns `:44`, so the search works on that file. `vm_bv(j,landcover44,potnatveg)` is declared at `modules/44_biodiversity/bv_btc_mar21/declarations.gms:19`.
- **reasoning**: Confirmed on both sub-errors: the cited range cannot support the `vm_bv` row, and the dimension label `landcover` should be `landcover44`. The auditor is scrupulous in noting the row's *substance* (M29 provides the two slices to M44) is correct, which is why Minor is right. The DECLARED-POPULATED-READ framing — M29 **populates** two slices but **declares** none of `vm_bv` — is the correct mental model and matches the MANDATE.
- **severity_agreed**: Minor

---

### F19: "Lines Analyzed: 444" — actual 440
- **verdict**: SURVIVES
- **my_independent_check**: `wc -l modules/29_cropland/detail_apr24/*.gms` run this session → equations.gms **123** (doc: 124), input.gms **103** (doc: 103 ✅), sets.gms **16** (doc: 17), presolve.gms **130** (doc: 131), preloop.gms **68** (doc: 69). True total **440**; doc claims 444 at `module_29.md:1103`.
- **reasoning**: Confirmed. Four of five components off by exactly +1, and `124+103+17+131+69` does sum to 444 — internally consistent arithmetic over wrong measurements. The auditor's restraint is right: negligible alone, Minor, and its real value is corroborative for F14 (numbers produced by recollection rather than measurement). Note `:6` hedges with "~", so only `:1103` is an unhedged false claim — the auditor flags this themselves.
- **severity_agreed**: Minor

---

## Tally

| Verdict | Count | Findings |
|---|---|---|
| SURVIVES | 18 | F1, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, F13, F14, F15, F16, F17, F18, F19 |
| PARTIALLY_REFUTED | 1 | F2 (Major → Minor) |
| REFUTED | 0 | — |

**Survivors by my agreed severity**: **Critical 2** (F1, F9) · **Major 12** (F3, F4, F5, F6, F7, F8, F10, F11, F12, F13, F14, F15) · **Minor 5** (F2-remnant, F16, F17, F18, F19).

## What the refutation pass changed

1. **F2 downgraded Major → Minor.** The doc *omits* the macro's `stockType` dispatch; it does not assert addition or "invert control flow". The auditor's reader-harm story is driven by F3 (which is flatly false and correctly Major), so pricing both at Major double-counts one harm through one root cause.
2. **F4's class refuted, finding intact.** Not `realization-contrast-confabulated-from-name`. Module 30 has *identically named* `detail_apr24`/`simple_apr24` realizations, and `modules/30_croparea/simple_apr24/realization.gms:8-10` says "**simplified rotational constraints**" while genuinely doing crop allocation (`q30_rotation_max/min`, `q30_crop_reg`). The sentence is a **cross-module transplant between homonymous realizations** — a different, more checkable, and more generalizable class.
3. **F8 strengthened; the auditor's flagged gap closed against them.** Both growth curves take the *same asymptote symbol* `fm_carbon_density(t,j,"secdforest",·)`; the `litc` expressions are character-identical; and `f52_growth_par.csv` gives plantations strictly higher `k` in every class where they differ. Plantation carbon density is **≥** natveg at every age class, converging to equality — never lower. The doc is inverted, not merely unsupported. Confidence medium-high → **high**.
4. **F13 strengthened; my best refutation failed.** The default config *does* carry a non-zero carbon price (`c56_pollutant_prices <- "R34M410-SSP2-NPi2025"`), which would have broken the dominance argument — but `c56_emis_policy <- "reddnatveg_nosoil"` sets `crop_vegc = crop_litc = crop_soilc = som = 0` in `f56_emis_policy.csv`. No carbon revenue reaches cropland tree cover at defaults. The auditor's acknowledged gap is now closed in their favour.
5. **F9 sub-count corrected upward**: `pm_avl_cropland_iso` has **5** consuming realizations, not 4. Undercount in the safe direction; conclusion unaffected.

## Where I think the auditor was over-eager

Only F2. Elsewhere the calibration is notably careful — F10's "the doc's check is numerically true, just wrongly attributed" nuance, F14's concession that the 16-formula claim is true, F19's note that `:6` hedges, and the Coverage-honesty section's explicit flagging of F8 and F13 as the weak points were all accurate self-assessments. Both weak points resolved **against** the doc on independent checking, which is evidence the auditor's uncertainty was honest rather than defensive hedging.
