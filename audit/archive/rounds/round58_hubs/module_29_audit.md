# M29 adversarial audit (R58)

**Target**: `modules/module_29.md` (1112 lines) vs `../modules/29_cropland/` @ develop `0d7ebeb90`
**Date**: 2026-07-17
**Auditor discipline**: all ground truth derived directly from `.gms` files read this session. No `scripts/check_*.py` artifact was read or consulted. All absence claims carry a positive control.

---

## Denominator

**claims_evaluated: 168**

What I counted as one claim: each independently checkable assertion — a variable/equation/parameter/set name, a formula, a `file:line` citation, a default value, a count, a producer/consumer attribution, a set-member list, a described mechanism, a data-flow direction.

Breakdown of the 168:
- Header/metadata block: 7
- Overview + Cropland Definition: 7
- Realization Differences (detail vs simple): 5
- Equations §1–§16 (formula correctness, citation accuracy, component attributions, interface targets): 65
- Key Algorithms 1–6 (pseudo-code fidelity, citations, switch semantics): 18
- Input Data Files table: 4
- Interface Variables tables (provided + used), incl. omission checks: 15
- Internal Variables table: 2
- Configuration Options tables (~20 defaults + 4 source citations): 24
- Scaling section: 2
- Participates In / conservation laws / dependency chains: 12
- Circular Dependencies: 5
- Limitations (only the 8 with a checkable code anchor): 8
- Verification Notes footer: 6 — minus 8 double-counted across sections = **168**

**Excluded from the denominator** (checked nothing, claimed nothing):
- Purely interpretive/editorial prose (e.g. "Key Position", "Hub Type: Aggregation Hub", "Rationale: Simulates continuous planting") — no code referent.
- 4 of the 12 Limitations that are pure modelling-philosophy statements with no falsifiable code anchor (#1, #7, #11, #12).
- "Modification Safety" prose (risk level, safe/dangerous lists, common issues) — advisory, not factual.
- Cross-doc pointers into `cross_module/*.md` (I verified `core_docs/Module_Dependencies.md` only, because module_29.md quotes a *number* from it).
- The two `.cs3`/`.cs2` input **file contents** (binary/large; I verified the declarations that read them, not the data).

**Verification outcome**: 149 claims verified correct, 19 defective.

---

## Findings

### F1: `pm_carbon_density_soilc` does not exist anywhere in MAgPIE; the "Cycle C29" back-edge it carries is fabricated

- **severity**: Critical
- **self_named_class**: `phantom-return-edge` — an invented interface name used as the closing arrow of a dependency *cycle* diagram, which upgrades a one-directional edge into a fictitious feedback loop
- **fits_existing_taxonomy**: partly. "Invented variable name presented as authoritative" is a named class. But the *structural* half is not: the fabricated name is load-bearing for a **topology** claim (M29 ↔ M59 is a cycle). The name and the cycle fail together, and a taxonomy that only flags the identifier misses that the doc asserts a feedback loop that does not exist. I'd name the compound class `phantom-return-edge`.
- **doc_location**: `modules/module_29.md:934-948` (diagram at :941)
- **doc_says**:
  > `#### Cycle C29: Cropland ↔ SOM (Temporal Feedback)`
  > `Module 29 (Cropland) ──→ vm_treecover(j) ──→ Module 59 (SOM)`
  > `       ↑                                          │`
  > `       └────────── pm_carbon_density_soilc ←──────┘`
  > `                  (soil carbon equilibrium)`
- **code_says**: `pm_carbon_density_soilc` **does not exist** in any `.gms` file in the repository. Furthermore M29 reads **nothing** produced by M59. M29's complete inbound set (from reading all of `detail_apr24/*.gms` this session) is: `vm_land`, `vm_area`, `vm_carbon_stock_croparea`, `vm_lu_transitions`, `pm_interest`, `pm_land_conservation`, `fm_carbon_density`, `fm_bii_coeff`, `fm_luh2_side_layers`, `pm_carbon_density_secdforest_ac_uncalib`, `pm_carbon_density_plantation_ac_uncalib`, `pm_land_hist`, `pcm_land`, and its own `f29_*`. None originate in M59. The M29→M59 relationship is a **one-way edge** (M59 consumes `vm_fallow` and `vm_treecover`), not a cycle.
- **code_evidence**:
  - Absence: `rg -n 'pm_carbon_density_soilc' --glob '*.gms' .` → zero matches. **Positive control**: the same command shape for `pm_land_start` returned 10 matches incl. `modules/10_land/landmatrix_dec18/declarations.gms:9`, so the search is functioning.
  - One-way edge confirmed: `modules/59_som/cellpool_jan23/equations.gms:25-26` (`vm_fallow(j2) * i59_cratio_fallow(j2)`, `vm_treecover(j2) * i59_cratio_treecover`); `modules/59_som/static_jan19/equations.gms:13-14`.
  - M29 inbound set: `modules/29_cropland/detail_apr24/equations.gms:1-123`, `preloop.gms:1-68`, `presolve.gms:1-131` (read in full).
- **why_it_matters**: The doc's own "Testing Protocol" (`:950-954`) and "Dangerous Modifications" (`:981`) instruct a modifier to check the M29↔M59 soil-carbon *convergence loop* before touching M29. There is no loop to check, and the parameter named as its channel is not a real symbol. A reader greps `pm_carbon_density_soilc`, finds nothing, and is left unable to distinguish "I searched wrong" from "the doc invented this" — the exact failure mode the anti-confabulation MANDATEs exist to prevent. Severity is Critical on two independent triggers: invented name presented as authoritative, and a wrong data-flow direction/dependency-set claim.
- **confidence**: high

---

### F2: `m_carbon_stock_ac` described as an additive sum over both `ac` and `ac_sub`; the macro is a mutually-exclusive dispatch on `stockType`

- **severity**: Major
- **self_named_class**: `macro-expansion-misread-as-arithmetic` — a `$(cond)`-guarded either/or expansion read as a `+` of two terms, because the expanded source *looks* like `A + B`
- **fits_existing_taxonomy**: **NO.** Existing classes cover fabricated formulas and wrong identifiers. This is neither: the doc quotes the macro *call site* correctly (`equations.gms:42`) and gets every identifier right. The defect is that the doc's prose gloss of what the macro *expands to* inverts its control flow. A checker that diffs the quoted formula against the source passes this cleanly — the error lives one indirection away, inside `core/macros.gms`, and only surfaces in the prose. I'd name it `macro-expansion-misread-as-arithmetic`.
- **doc_location**: `modules/module_29.md:181-183`
- **doc_says**:
  > **Age-Class Macro** (`m_carbon_stock_ac`):
  > - Sums carbon across age classes (ac) and subset (ac_sub)
- **code_says**: The macro's two terms are **mutually exclusive**, selected by the `stockType` index, not added:
  ```gams
  $macro m_carbon_stock_ac(land,carbon_density,sets,sets_sub) \
     sum((&&sets),     land(j2,&&sets)     * sum(ct, carbon_density(ct,j2,&&sets,ag_pools)))$(sameas(stockType,"actual")) + \
     sum((&&sets_sub), land(j2,&&sets_sub) * sum(ct, carbon_density(ct,j2,&&sets_sub,ag_pools)))$(sameas(stockType,"actualNoAcEst"))
  ```
  For `stockType="actual"` the second term is 0 and the stock sums over **all** `ac`. For `stockType="actualNoAcEst"` the first term is 0 and the stock sums over `ac_sub` only (**excluding** newly established age classes). The `+` is a GAMS idiom for branch selection, not accumulation.
- **code_evidence**: `core/macros.gms:104-106`; call site `modules/29_cropland/detail_apr24/equations.gms:42`; `stockType` set at `modules/56_ghg_policy/price_aug22/sets.gms:212-213`.
- **why_it_matters**: A reader who trusts "sums across ac **and** ac_sub" concludes cropland tree-cover carbon **double-counts** the mature age classes (once in the `ac` sum, once in the `ac_sub` sum) — i.e. that `q29_carbon` is buggy. It isn't. Conversely, the reader never learns the actual purpose of the macro: the `actualNoAcEst` stock type is what lets the GHG-policy module exclude establishment-year carbon from emission accounting. Getting this backwards misdirects any carbon-accounting or MACC investigation touching cropland.
- **confidence**: high

---

### F3: `stockType` glossed as "Actual vs reference stocks"; the set has no "reference" member

- **severity**: Major
- **self_named_class**: `plausible-set-member-substitution` — a real set given a *semantically reasonable but invented* member vocabulary that displaces the real one
- **fits_existing_taxonomy**: yes-ish (exact set-member labels MANDATE), though note the failure mode is not a typo: "reference" is a term that exists elsewhere in MAgPIE carbon accounting, which is precisely why it reads as correct.
- **doc_location**: `modules/module_29.md:186`
- **doc_says**: "**Stock Types** (stockType): Actual vs reference stocks"
- **code_says**: `stockType Carbon stock types / actual, actualNoAcEst /` — the two members are `actual` and `actualNoAcEst`. There is no `reference` member. The distinction is *all age classes* vs *excluding establishment age classes*, not actual-vs-reference.
- **code_evidence**: `modules/56_ghg_policy/price_aug22/sets.gms:212-213`
- **why_it_matters**: Directly compounds F2 — with `stockType` misdefined, the reader has no way to recover the real meaning of the `m_carbon_stock_ac` branch even if they doubt the prose. Anyone writing a `$(sameas(stockType,"reference"))` guard against `vm_carbon_stock` gets a silently empty expression (GAMS does not error on `sameas` with a non-member string literal) — a zero that looks like data.
- **confidence**: high

---

### F4: `simple_apr24` characterized as "simplified crop allocation without rotational constraints" — both halves fabricated

- **severity**: Major
- **self_named_class**: `realization-contrast-confabulated-from-name` — the difference between two realizations invented from the word "simple" rather than read from either realization's code
- **fits_existing_taxonomy**: **NO.** This is not "describing a non-default realization as active" (the doc correctly marks `detail_apr24` as default throughout). It is a fabricated *contrast axis*: the doc invents a dimension on which the realizations differ, and that dimension exists in neither. The class is specific to multi-realization modules and is invisible to any single-realization reading — you only catch it by reading the realization the doc *isn't* about.
- **doc_location**: `modules/module_29.md:12`
- **doc_says**: "Alternative `simple_apr24` uses simplified crop allocation without rotational constraints."
- **code_says**: Both halves are false.
  1. **"crop allocation"**: `simple_apr24` performs no crop allocation. Its `q29_cropland` merely equates `vm_land(j2,"crop")` to `sum((kcr,w), vm_area(j2,kcr,w))`. Crop allocation is Module 30's job in *both* realizations.
  2. **"rotational constraints"**: the token `rotation` appears **nowhere** in `modules/29_cropland/` in either realization. **Positive control**: `rg -nic 'cropland' modules/29_cropland/detail_apr24/input.gms` → 24 matches, so the search path is live.
  The actual, code-stated difference (`simple_apr24/realization.gms:8-12`): *"total cropland equals croparea because fallow land and tree cover on cropland are fixed to zero… Biodiversity BII values are fixed to zero. Costs are fixed to zero."* Mechanically: `simple_apr24/preloop.gms:8-12` does `vm_cost_cropland.fx(j)=0; vm_fallow.fx(j)=0; vm_treecover.fx(j)=0; vm_bv.fx(j,"crop_fallow",potnatveg)=0; vm_bv.fx(j,"crop_tree",potnatveg)=0;`.
- **code_evidence**: `modules/29_cropland/simple_apr24/equations.gms:12-13`; `simple_apr24/realization.gms:8-12`; `simple_apr24/preloop.gms:8-12`; `rg -ni 'rotation' modules/29_cropland/` → no match (positive control above).
- **why_it_matters**: This sentence sits in the **default-realization callout box at the top of the doc** — the highest-trust real estate in the file, and the one place a hurried reader looks to decide whether the default is right for them. A reader choosing a realization is told the trade-off is "crop-rotation fidelity", so they may stay on `detail_apr24` to keep rotations they were never going to lose, or switch to `simple_apr24` for speed without learning that they are silently zeroing out fallow, tree cover, all cropland costs, and two BII land-cover classes. There is also a secondary hazard: the doc's `vm_bv → Module 44` interface claim is realization-conditional in a way the doc never states — under `simple_apr24` both `vm_bv` slices are pinned to 0.
- **confidence**: high

---

### F5: "Fallow only used when target > 0" — the actual gate is `s29_fallow_max`, which is 0 by default and hard-zeroes fallow regardless of any target

- **severity**: Major (rubric says pick the lower tier when between; I am genuinely between Major and Critical — see below)
- **self_named_class**: `false-enabling-condition` — the doc names the wrong switch as the one that turns a mechanism on, while correctly reporting the real switch's value two lines earlier
- **fits_existing_taxonomy**: **NO.** "Missing default-state caveat" doesn't fit: the caveat is *present and correct* at `:297`. The defect is that the very next line asserts an enabling condition that contradicts it. The doc contains both the truth and its negation, adjacent, and the negation is the actionable sentence. I'd call the class `false-enabling-condition`, and note the aggravating structure: **local self-contradiction where the wrong half is the operative instruction.**
- **doc_location**: `modules/module_29.md:299` (contradicting `:297`)
- **doc_says**:
  > `:297` **Default** (`input.gms:33`): `s29_fallow_max = 0` (no fallow allowed by default)
  > `:299` **Note**: Fallow only used when target > 0 or other policies incentivize it
- **code_says**: `q29_fallow_max` is **unconditional** — it has no `$(...)` guard and is active in every cell, every timestep:
  ```gams
  q29_fallow_max(j2) ..  vm_fallow(j2) =l= vm_land(j2,"crop") * s29_fallow_max;
  ```
  With `s29_fallow_max = 0` (default), this forces `vm_fallow(j2) =l= 0`; combined with `vm_fallow` being a **positive variable** (`declarations.gms:44`) and `vm_fallow.lo(j)=0` (`presolve.gms:120`), fallow is **identically zero** under the default config. Setting `s29_fallow_target > 0` does **not** enable fallow. It makes `i29_fallow_target(t)` positive (`presolve.gms:104`), which activates `q29_fallow_min` (`equations.gms:66-68`) and forces `v29_fallow_missing(j2) =g= vm_land(j2,"crop") * i29_fallow_target(ct) - 0`, which then enters the objective at `i29_fallow_penalty = s29_fallow_penalty = 615` USD17MER/ha (`presolve.gms:110`, `input.gms:34`) via `q29_cost_cropland` (`equations.gms:31`). The **necessary** switch is `s29_fallow_max > 0`.
- **code_evidence**: `modules/29_cropland/detail_apr24/equations.gms:70-72` (`q29_fallow_max`, unguarded); `equations.gms:66-68` (`q29_fallow_min`); `equations.gms:31` (penalty enters cost); `declarations.gms:44`; `input.gms:33-34`; `presolve.gms:104,110,120`.
- **why_it_matters**: This is the doc's only actionable guidance on how to run a fallow scenario, and it is wrong in the damaging direction. A user sets `s29_fallow_target <- 0.2`, runs the model, and gets: **0% fallow** (unchanged land allocation) **plus** an unbudgeted `0.2 × vm_land(j,"crop") × 615 USD/ha` cost term added to the objective in every cell from 2025 onward. The run **solves cleanly**. There is no warning, no infeasibility, no error — just a large, spatially-varying, entirely spurious cost that distorts every land-allocation margin in the model, and a "fallow scenario" that contains no fallow. That is a wrong high-stakes action producing silently corrupted results, which is the Critical trigger. I am holding at Major only because `:297` states the correct default value two lines above, giving an attentive reader a thread to pull. A reader who reads `:299` as the summary — which is exactly what a "**Note**:" line invites — gets no such thread.
- **confidence**: high

---

### F6: `v29_treecover` presented as fully optimized; in fact only `ac_est` slices are free — `ac_sub` is `.fx`'d to the previous timestep

- **severity**: Major
- **self_named_class**: `presolve-bound-erases-decision-variable` — a variable the doc calls a decision variable is fixed by a `.fx` in presolve for most of its index domain, so the "optimization" is over a small subset of the declared slices
- **fits_existing_taxonomy**: **NO.** The variable name, dimensions, declaration, and every equation containing it are correct in the doc. The defect is that a **presolve `.fx` statement silently removes most of the variable's degrees of freedom**, and the doc never mentions it. This class is structurally invisible to equation-level verification — `equations.gms` is 100% consistent with the doc — and only appears if you read `presolve.gms` looking for bounds. I'd name it `presolve-bound-erases-decision-variable`. I suspect it generalizes well beyond M29 (any module whose presolve `.fx`/`.up`/`.lo` narrows a variable the docs call "optimized").
- **doc_location**: `modules/module_29.md:95` (also `:37`, `:381-384`)
- **doc_says**:
  > `:95` `v29_treecover(j,ac)` - Tree cover by age class (**optimized in this module**) — **detail_apr24 only**
  > `:37` Tree cover on cropland (age-class dynamics, **optimized** with targets/penalties)
- **code_says**: `presolve.gms:78-82`, under the explicit comment *"Bounds for treecover. Only ac_est can increase in optimization. ac_sub is fixed."*:
  ```gams
  v29_treecover.lo(j,ac_est) = 0;
  v29_treecover.up(j,ac_est) = Inf;
  v29_treecover.fx(j,ac_sub) = pc29_treecover(j,ac_sub);
  m_boundfix(v29_treecover,(j,ac_sub),l,1e-6);
  ```
  Only the **establishment** age classes are decision variables. All non-establishment slices are pinned to `pc29_treecover(j,ac_sub)` — the previous timestep's age-shifted state (`presolve.gms:57-62`, `postsolve.gms:8`). The optimizer can **plant** trees but can never **remove** them.
- **code_evidence**: `modules/29_cropland/detail_apr24/presolve.gms:78-82`; age-shift `presolve.gms:55-62`; carry-forward `postsolve.gms:8`; `ac_est`/`ac_sub` at `core/sets.gms:277,279`.
- **why_it_matters**: This is the single most important structural fact about tree cover in M29, and the doc omits it while asserting its opposite. Consequences for a trusting reader: (a) they expect `q29_treecover_max` (`s29_treecover_max = 1`) to be the binding ceiling on tree cover, when in practice the binding structure is "existing stock is frozen, only new planting is free"; (b) they cannot explain why tree cover never declines in output; (c) they will misread `q29_cost_treecover_recur` — the `ac_sub` term is a **fixed** cost given the state, not a marginal one, so it cannot influence the planting decision at all, which is a non-obvious and consequential asymmetry with `q29_cost_treecover_est`. Note the doc *does* get the downstream consequence right at Limitation #8 ("Once established, tree cover cannot be harvested") while attributing it to "no equations for tree removal" — the real cause is this `.fx`. So the doc knows the symptom and misattributes the mechanism.
- **confidence**: high

---

### F7: BII-coefficient switch `s29_treecover_bii_coeff` is inert for all years ≤ `sm_fix_SSP2` (=2025); doc omits the guard

- **severity**: Major
- **self_named_class**: `switch-documented-outside-its-temporal-gate`
- **fits_existing_taxonomy**: partly — "missing default-state caveat" is close, but this is a *temporal* gate rather than a default value: the switch is honoured only after a year threshold set in a **different module's config key**. I'd name it `switch-documented-outside-its-temporal-gate`.
- **doc_location**: `modules/module_29.md:404-409`
- **doc_says**:
  > **Switch** (`s29_treecover_bii_coeff`):
  > - `0` (default): Use secondary vegetation BII coefficients
  > - `1`: Use timber plantation BII coefficients
  Presented unconditionally.
- **code_says**: the switch is wrapped in a year guard that the doc does not mention:
  ```gams
  if(m_year(t) <= sm_fix_SSP2,
   p29_treecover_bii_coeff(bii_class_secd,potnatveg) = fm_bii_coeff(bii_class_secd,potnatveg)
  else
   if(s29_treecover_bii_coeff = 0, ... = fm_bii_coeff(bii_class_secd,potnatveg)
   elseif s29_treecover_bii_coeff = 1, ... = fm_bii_coeff("timber",potnatveg) );
  );
  ```
  For every timestep with `m_year(t) <= sm_fix_SSP2`, the secondary-vegetation coefficients are used **regardless of the switch**. `sm_fix_SSP2 = 2025` by default (`config/default.cfg:225`); `scripts/start/extra/input_REMIND.R:40` sets it to 2020 for coupled runs.
- **code_evidence**: `modules/29_cropland/detail_apr24/presolve.gms:44-52`; `config/default.cfg:225`; `scripts/start/extra/input_REMIND.R:40`.
- **why_it_matters**: A reader setting `s29_treecover_bii_coeff <- 1` and comparing 2020/2025 BII output against a baseline sees **no difference** and concludes the switch is broken, or worse, concludes their scenario has no BII effect. The guard also means the switch's effective start year silently moves (2025 standalone vs 2020 REMIND-coupled) — a cross-config gotcha that is discoverable only from this line.
- **confidence**: high

---

### F8: Plantation growth curve claimed to converge to a *lower* final carbon density; the code comment says both curves converge to LPJmL natural vegetation

- **severity**: Major
- **self_named_class**: `domain-plausible-tradeoff-overwriting-code-comment` — a real-world ecological trade-off ("plantations grow fast but store less") asserted over an adjacent code comment that explicitly denies the second half
- **fits_existing_taxonomy**: **NO.** This is not a fabricated formula or a wrong identifier — the doc's code quotes at `:642` and `:650` are correct. It is the CLAUDE.md "MAgPIE accounts for X" hazard inverted: instead of promoting parameterization to mechanism, the doc imports a **domain-textbook trade-off** the model does not implement, and the refuting evidence is a comment sitting three lines above the code the doc quoted. I'd name the class `domain-plausible-tradeoff-overwriting-code-comment`. It is the most insidious kind here because the claim is ecologically true in general and false for this model.
- **doc_location**: `modules/module_29.md:653-656`
- **doc_says**:
  > - Converges to plantation carbon density (typically lower than natural)
  > **Trade-off**: Plantation grows faster initially but has lower final carbon density
- **code_says**: `preloop.gms:42-44`, immediately above the `if` block the doc quotes:
  ```
  *' Switch for tree cover on cropland:
  *' 0 = Use natveg growth curve towards LPJmL natural vegetation
  *' 1 = Use plantation growth curve (faster than natveg) towards LPJmL natural vegetation
  ```
  Both options converge **towards LPJmL natural vegetation**. The code affirms only the *speed* difference ("faster than natveg"); it explicitly states the same asymptote for both. The doc's "lower final carbon density" and the framed "**Trade-off**" have no support in M29, and M29 does not compute the asymptote at all — it copies `pm_carbon_density_{secdforest,plantation}_ac_uncalib` wholesale from M52 (`52_carbon/normal_dec17/start.gms:43-44`).
- **code_evidence**: `modules/29_cropland/detail_apr24/preloop.gms:42-49`; `modules/52_carbon/normal_dec17/declarations.gms:10,13`; `modules/52_carbon/normal_dec17/start.gms:43-44`.
- **why_it_matters**: A reader deciding `s29_treecover_plantation` is told they are trading early sequestration against long-run stock. Per the code comment, they are not — they are choosing a *rate* toward the same endpoint. Under a carbon price (M56), that misframing inverts the expected sign of the long-run result and would send someone hunting a nonexistent bug when plantation and natveg runs converge late-century. **Uncertainty I am flagging rather than dropping**: I verified the code's *comment*, not the *numerical content* of the two `_ac_uncalib` arrays (they are populated in M52 from LPJmL input data I did not parse). If the plantation array in fact plateaus lower, the doc's claim would be accidentally true while still being unsupported by anything in M29 and contradicted by the authoring comment. Reported as a defect on the evidence available; the residual is on the array values, not on the reading.
- **confidence**: medium-high (code comment: high; array values: unverified — see Coverage honesty)

---

### F9: The "Provides To" set is wrong — two produced interfaces omitted entirely, two descriptions fabricated, five consumer modules hidden behind a hedge

- **severity**: Critical (wrong producer/consumer set — Critical by stated precedent)
- **self_named_class**: `hedge-as-coverage-substitute` — a vague quantifier ("plus potentially 1-2 other modules") standing in for unenumerated real consumers, which converts a checkable claim into an uncheckable one and thereby **defeats validation rather than failing it**
- **fits_existing_taxonomy**: the wrong-consumer-set part, yes. The hedge, **NO** — and it is the more interesting half. A wrong list is falsifiable; "plus potentially 1-2 other modules" is *engineered to be unfalsifiable* while reading as diligence. It also happens to be numerically wrong (the gap is 5, not 1-2). I'd name it `hedge-as-coverage-substitute` and flag it as a class worth grepping for corpus-wide, since it is a *style* that suppresses audit signal.
- **doc_location**: `modules/module_29.md:889-895` (and the "Provided by Module 29" table at `:679-686`)
- **doc_says**:
  > **Provides To** (6 modules):
  > 3. **Module 52 (Carbon)** … 4. **Module 59 (SOM)** - Soil organic matter targets for cropland
  > 5. **Module 22 (Conservation)** - Protected cropland area (if applicable)
  > 6. Plus potentially 1-2 other modules
- **code_says**: Four separate errors.
  1. **`pm_avl_cropland_iso` omitted entirely.** M29 *declares* it (`declarations.gms:20`) and *populates* it (`preloop.gms:58`, in **both** realizations). It is read by **three other modules, four realizations**: `13_tc/endo_jan22/presolve.gms:49,59`; `13_tc/exo/presolve.gms:25,35`; `30_croparea/detail_apr24/preloop.gms:41`; `30_croparea/simple_apr24/preloop.gms:25`; `59_som/cellpool_jan23/preloop.gms:110`. M29 is the sole producer. The doc's Provided table never lists it, and **Modules 13 and 30 appear nowhere** in the doc's downstream set.
  2. **`vm_carbon_stock` omitted from the Provided table.** `q29_carbon` writes `vm_carbon_stock(j2,"crop",ag_pools,stockType)` (`equations.gms:38-42`); it is read by `52_carbon/normal_dec17/equations.gms:19` and `56_ghg_policy/price_aug22/postsolve.gms:11-53`. The doc's dependency *list* mentions M52 at `:892` but the interface *table* at `:679-686` omits the variable — the two disagree.
  3. **"Module 59 - Soil organic matter targets for cropland" is fabricated.** M29 provides M59 with `vm_fallow` and `vm_treecover`. It does not provide SOM targets; M59 computes `v59_som_target` itself (`59_som/cellpool_jan23/equations.gms:48`).
  4. **"Module 22 - Protected cropland area (if applicable)" is fabricated, and the arrow is backwards.** M29 provides M22 with `vm_treecover` (`22_land_conservation/area_based_apr22/presolve_ini.gms:87,98,109`). "Protected cropland area" travels the *other* way: M22 → M29 via `pm_land_conservation`, which the doc itself correctly documents at `:697` and `:800`.
  The true outward set is at minimum **{10, 11, 13, 22, 30, 32, 44, 50, 52, 56, 59}** ≈ 11 modules. The doc names 5 and hedges 1-2.
- **code_evidence**: `modules/29_cropland/detail_apr24/declarations.gms:20`; `detail_apr24/preloop.gms:58`; `simple_apr24/preloop.gms:35`(=preloop tail line 28); `modules/13_tc/endo_jan22/presolve.gms:49,59`; `modules/13_tc/exo/presolve.gms:25,35`; `modules/30_croparea/detail_apr24/preloop.gms:41`; `modules/30_croparea/simple_apr24/preloop.gms:25`; `modules/59_som/cellpool_jan23/preloop.gms:110`; `modules/52_carbon/normal_dec17/equations.gms:19`; `modules/29_cropland/detail_apr24/equations.gms:38-42`; `modules/59_som/cellpool_jan23/equations.gms:48`; `modules/22_land_conservation/area_based_apr22/presolve_ini.gms:87,98,109`.
- **why_it_matters**: This is the doc's blast-radius map, and the doc rates M29 🔴 HIGH RISK specifically so that readers consult it before modifying. Someone changing `c29_marginal_land` reads "Provides To: 10, 11, 52, 59, 22" and never learns that `pm_avl_cropland_iso` — the *same* `f29_avl_cropland_iso(iso,"%c29_marginal_land%")` lookup — is the denominator of the country-weighting in **Modules 13 and 30**. That switch silently re-weights technological-change costs and croparea policy targets in two modules the doc says are unaffected. This is exactly the failure the "wrong producer/consumer set is Critical" precedent exists to catch.
- **confidence**: high

---

### F10: M10's land balance quoted as `sum(land, vm_land(j,land)) = pm_land_start(j)`; the actual equation `q10_land_area` closes against `pcm_land`

- **severity**: Major
- **self_named_class**: `invariant-restated-with-wrong-anchor` — a conservation law quoted with the wrong right-hand parameter and stripped of a dimension, propagated verbatim into a testing checklist
- **fits_existing_taxonomy**: partly (wrong parameter / citation drift), but the propagation is the notable part: the same malformed expression appears **three times**, twice inside "✅ Verify:" checklist items, so the error is not a stray sentence but the doc's prescribed acceptance test.
- **doc_location**: `modules/module_29.md:932`, `:951`, `:985`
- **doc_says**:
  > `:932` Module 10 ensures total land balance: `sum(land, vm_land(j,land)) = pm_land_start(j)`
  > `:951` ✅ Verify land balance: `sum(land, vm_land(j,land)) = pm_land_start(j)`
  > `:985` - Verify: `sum(land, vm_land(j,land)) = pm_land_start(j)` for all cells
- **code_says**:
  ```gams
  q10_land_area(j2) ..
    sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));
  ```
  The balance closes against **`pcm_land`** (previous timestep's land state), not `pm_land_start` (the 1995 initialization, `10_land/start.gms:8`). The doc also drops the `land` index and the outer `sum` from the RHS: `pm_land_start(j)` is not a valid reference — the parameter is `pm_land_start(j,land)` (`10_land/landmatrix_dec18/declarations.gms:9`). The equation name `q10_land_area` is never given.
  *Nuance, stated so as not to overclaim*: because `q10_land_area` conserves the per-cell total every step and `pcm_land` is seeded from `pm_land_start` (`10_land/start.gms:11`), the *scalar total* `sum(land, pm_land_start(j,land))` does numerically equal `sum(land, vm_land(j,land))` at every timestep. So the doc's check is not numerically wrong — it is **wrongly attributed and malformed**, and it tests a weaker invariant (the constant total) than the one M10 actually enforces (closure against the immediately preceding state).
- **code_evidence**: `modules/10_land/landmatrix_dec18/equations.gms:13-15`; `modules/10_land/landmatrix_dec18/declarations.gms:9`; `modules/10_land/landmatrix_dec18/start.gms:8,11`.
- **why_it_matters**: A reader implementing the doc's Testing Protocol writes `pm_land_start(j)` into a GAMS display or an R check and gets a **domain error** (dimension mismatch) — the cheap failure. The expensive failure is conceptual: they believe M10's invariant is "total land equals its 1995 value", miss that the real constraint is timestep-to-timestep closure, and therefore do not know where to look when a land-balance violation appears mid-run. Since M29 is the module most likely to break that balance (it *defines* `vm_land(j,"crop")`), pointing its modifiers at the wrong invariant is a real cost.
- **confidence**: high

---

### F11: "Total Connections: 12 (provides to 6, depends on 6)" contradicts the source the doc cites, which says 13 (6 / 7); the section pointer is also wrong

- **severity**: Major (fabricated count)
- **self_named_class**: `citation-laundered-number` — a number attributed to a named authoritative source that does not match that source, where the citation confers the credibility that discourages the check
- **fits_existing_taxonomy**: "fabricated count" covers the number. The laundering — that a *correct-looking* pointer to a real, real-authoritative file is what makes the wrong number survive — is not a class I've seen named, and it is the reason this defect persists: the number looks sourced.
- **doc_location**: `modules/module_29.md:885-886`, `:907`
- **doc_says**:
  > **Centrality Rank**: 9 of 46
  > **Total Connections**: 12 (provides to 6, depends on 6)
  > `:907` **Reference**: `core_docs/Module_Dependencies.md` (Section 3.1, Centrality Rankings)
- **code_says** (doc-vs-cited-source, plus doc-vs-code):
  - `core_docs/Module_Dependencies.md:39` → `| 9 | **29_cropland** | 13 | 6 | 7 | Cropland management |` under header `| Rank | Module | Total | Provides To | Depends On |`. So the cited source says **Total 13, provides 6, depends 7** — not 12 / 6 / 6. Rank 9 ✅ is the only part that matches.
  - The section pointer is wrong: the Centrality Rankings table is at **§1.2** (`Module_Dependencies.md:25`), not §3.1.
  - Independently, **both numbers understate reality**. Per F9 the true outward degree alone is ~11 modules. Neither 12 nor 13 is defensible against the code.
- **code_evidence**: `core_docs/Module_Dependencies.md:25,29-39`; outward-degree evidence as itemized in F9.
- **why_it_matters**: Centrality is the doc's stated gate for modification risk ("Always check centrality before modifications", `Module_Dependencies.md:357`). A reader who follows `:907` to §3.1 finds no such table and must hunt; a reader who trusts `12 (6/6)` carries a blast-radius estimate that is wrong against both the cited source *and* the code. Note `Module_Dependencies.md:425` explicitly warns that recomputed counts must be propagated to dependents — this is that drift, already realized.
- **confidence**: high

---

### F12: Downstream section assigns `vm_fallow` and `vm_treecover` to Module 44, contradicting the doc's own interface table and the code

- **severity**: Major
- **self_named_class**: `intra-document-attribution-drift` — two tables in one file assert incompatible consumer sets for the same variables; a reader has no way to know which is authoritative
- **fits_existing_taxonomy**: the wrong-consumer half, yes. The *self-inconsistency* is the diagnostic: this defect is detectable **without reading any code at all**, purely by cross-reading `:682-683` against `:810-814`. That it survived a prior audit suggests section-local reading; a within-doc consistency pass would have caught it for free.
- **doc_location**: `modules/module_29.md:810-814` (contradicting `:682-683`)
- **doc_says**:
  > `:810` 3. **Module 44 (Biodiversity)**:
  > `:811`    - `vm_fallow(j)` - Fallow land area
  > `:812`    - `vm_treecover(j)` - Tree cover area
  > `:813-814`    - `vm_bv(j,"crop_fallow"…)`, `vm_bv(j,"crop_tree"…)`
  versus its own table:
  > `:682` `vm_fallow` … Used By: Modules 32 (Forestry), 50 (NR Soil Budget), 59 (SOM)
  > `:683` `vm_treecover` … Used By: Modules 22 (Conservation), 59 (SOM)
- **code_says**: The table (`:682-683`) is **correct**; the downstream list (`:811-812`) is **wrong**. Module 44 reads neither variable. Exhaustive grep for both equation-form `vm_x(` and solution-form `vm_x.`:
  - `vm_fallow` outside M29 → `59_som/static_jan19/equations.gms:13`; `59_som/cellpool_jan23/equations.gms:25`; `32_forestry/dynamic_may24/presolve.gms:18`; `50_nr_soil_budget/macceff_aug22/equations.gms:26`. **{32, 50, 59}** — no M44.
  - `vm_treecover` outside M29 → `22_land_conservation/area_based_apr22/presolve_ini.gms:87,98,109`; `59_som/cellpool_jan23/equations.gms:26`; `59_som/static_jan19/equations.gms:14`. **{22, 59}** — no M44.
  M44 touches M29 only through `vm_bv` (`:813-814` is correct) — and `vm_bv` is **declared in M44**, not M29 (`44_biodiversity/bv_btc_mar21/declarations.gms:19`), with M29 populating only the `crop_fallow` / `crop_tree` slices via `q29_fallow_bv` / `q29_treecover_bv`.
  **Positive control** for the grep: the same pattern run inside M29 returned `detail_apr24/postsolve.gms:17,41,65,89` and `preloop.gms:62`, confirming both paren- and dot-forms match.
- **code_evidence**: as listed above; `modules/29_cropland/detail_apr24/equations.gms:76-78,101-104`; `modules/44_biodiversity/bv_btc_mar21/declarations.gms:19`.
- **why_it_matters**: A reader tracing biodiversity impacts concludes M44 consumes fallow and tree-cover *areas* directly and goes looking for area terms in `44_biodiversity/*/equations.gms` that do not exist. The real coupling is exclusively through the pre-multiplied `vm_bv` slices — which matters, because it means M29 owns the BII coefficient choice (F7) and M44 only aggregates. Someone trying to change how fallow is valued in biodiversity would edit the wrong module.
- **confidence**: high

---

### F13: The doc never states that, under `config/default.cfg`, fallow and tree cover are both identically zero — making `detail_apr24` behaviourally equivalent to `simple_apr24`

- **severity**: Major
- **self_named_class**: `headline-mechanism-inert-at-defaults` — the module's advertised "Key Innovation" is switched off in the default configuration, disclosed only as scattered zeros in a config table 700 lines below the claim
- **fits_existing_taxonomy**: "Missing default-state caveat" names it, but understates the scope. This is not one missing caveat on one parameter — it is that the doc's **entire framing** (Overview, Key Innovation, Realization Differences, and 11 of 16 equation sections) describes machinery that produces zero under defaults, while the disclosure exists only as unremarked `0`s in tables at `:735-736`, `:746`, `:766-767`. The atoms are all individually true; the *emergent* claim is false. I'd name the class `headline-mechanism-inert-at-defaults` and note it is invisible to per-claim checking by construction — every checkable claim passes.
- **doc_location**: `modules/module_29.md:21` (and `:17`, `:31-41`)
- **doc_says**:
  > `:21` **Key Innovation**: Endogenizes fallow land and tree cover on cropland with flexible policy implementation…, allowing landscape heterogeneity within agricultural areas.
  > `:33` **What**: Full implementation with fallow land, tree cover dynamics, and SNV policy
- **code_says**: With `config/default.cfg:811` (`cropland <- "detail_apr24"`) and M29's stock defaults, all three policies are off and both endogenous quantities are pinned to zero:
  - **Fallow ≡ 0**: `s29_fallow_max = 0` (`input.gms:33`) ⇒ `q29_fallow_max` forces `vm_fallow =l= 0`; `vm_fallow` is positive with `.lo = 0` ⇒ exactly 0 in every cell, every timestep. (See F5.)
  - **Tree cover ≡ 0**: `s29_treecover_map = 0` (`input.gms:35`) ⇒ `pc29_treecover(j,ac) = 0` (`preloop.gms:37-38`) ⇒ the presolve age-shift propagates zeros and `v29_treecover.fx(j,ac_sub) = 0` (`presolve.gms:81`). `ac_est` remains free, but `s29_treecover_target = 0` (`input.gms:24`) ⇒ `i29_treecover_target = 0` ⇒ `q29_treecover_min` yields `v29_treecover_missing =g= 0` ⇒ no penalty is avoidable by planting. Planting is therefore strictly dominated: it costs `s29_cost_treecover_est = 2460` USD/ha annuitized plus `s29_cost_treecover_recur = 615` USD/ha/yr, consumes scarce cropland via `q29_cropland`, and yields zero offsetting benefit inside M29. The optimizer sets it to 0.
  - **SNV off**: `s29_snv_shr = s29_snv_shr_noselect = 0` (`input.gms:12-13`) ⇒ `p29_snv_shr = 0` ⇒ `q29_land_snv` reduces to the pre-existing `pm_land_conservation` bound and `p29_avl_cropland = f29_avl_cropland` unreduced (`presolve.gms:35`).
  Net: under defaults `q29_cropland` collapses to `vm_land(j,"crop") = sum((kcr,w), vm_area(j,kcr,w))` — **exactly `simple_apr24`'s `q29_cropland`** (`simple_apr24/equations.gms:12-13`) — and `q29_carbon` collapses to `vm_carbon_stock = vm_carbon_stock_croparea`, exactly `simple_apr24/equations.gms:29-31`.
- **code_evidence**: `config/default.cfg:811`; `modules/29_cropland/detail_apr24/input.gms:12-13,24,33,35`; `detail_apr24/equations.gms:12,38-42,66-72,90-96`; `detail_apr24/preloop.gms:37-38`; `detail_apr24/presolve.gms:35,81`; `modules/29_cropland/simple_apr24/equations.gms:12-13,29-31`.
- **why_it_matters**: The reader's takeaway from the top of the doc is "M29 is the module that endogenizes fallow and agroforestry." The operational truth is "M29 *can* do that, but out of the box it is an accounting identity for croparea." Two concrete harms: (a) a user diffing a `detail_apr24` run against `simple_apr24` to 'measure the effect of fallow and tree cover' gets a null result and hunts for a bug that isn't there; (b) a user reading the "Key Innovation" line believes their baseline already contains agroforestry dynamics and interprets downstream carbon/biodiversity results accordingly. This finding is the umbrella that F5 sits under — F5 is the sharp, actionable instance; F13 is the framing failure that let it through. Held at Major rather than Critical only because the individual default values *are* stated correctly in the config tables.
- **confidence**: high

---

### F14: The doc certifies itself defect-free — "No Errors Found: Zero discrepancies", "100% verified", "All 16 formulas match exactly"

- **severity**: Major
- **self_named_class**: `self-certifying-verification-banner` — an unfalsifiable clean-bill-of-health assertion that **transfers the doc's residual risk onto the reader while suppressing the scepticism that would surface it**
- **fits_existing_taxonomy**: **NO**, and I think this is the most structurally important finding in the round after F1/F9. Every other class here describes a claim *about MAgPIE*. This one is a claim *about the document*, and it is the claim that makes all the others more dangerous: a reader who sees "Zero discrepancies between code and documentation" and "Verification Status: 100% verified" rationally lowers their guard — which is precisely when F5's false enabling condition or F1's phantom parameter does its damage. The banner is also **self-refuting on the evidence of this audit**: 19 defects, of which 2 are Critical. Worth noting the meta-point for the round: these banners are *negatively* correlated with accuracy here, because they mark docs whose verification was declared rather than performed.
- **doc_location**: `modules/module_29.md:3`, `:1090-1097`, `:1104`
- **doc_says**:
  > `:3` **Status**: ✅ Fully Verified
  > `:1090` **Formula Accuracy**: ✅ All 16 equation formulas match source code exactly
  > `:1095` **Code Truth Compliance**: ✅ All claims verified against source code
  > `:1097` **No Errors Found**: Zero discrepancies between code and documentation
  > `:1104` **Verification Status**: 100% verified
- **code_says**: Falsified by F1–F13 and F15–F19 of this audit. Two sub-claims are individually checkable and split:
  - "**All 16 equation formulas match source code exactly**" — this one is **true**. I verified all 16 `q29_*` formulas character-by-character against `equations.gms:11-123`, and all 16 declarations against `declarations.gms:49-64`. The count of 16 is correct.
  - "**Zero discrepancies between code and documentation**" / "**All claims verified**" / "**100% verified**" — **false**. The defects cluster precisely *outside* the equation blocks: in macro semantics (F2), set members (F3), presolve bounds (F6, F7), realization contrast (F4), interface sets (F9, F12), and cross-module invariants (F10). The banner's scope creep from a true narrow claim ("formulas match") to a false total claim ("zero discrepancies") is the defect.
  - "**Citation Density: 80+ file:line citations**" (`:1094`) — not verifiable as stated and appears inflated: §6-§16 cite a bare `equations.gms` with **no line number** (`:229`, `:238`, `:252`, `:258`, `:281`, `:305`, `:322`, `:328`, `:344`, `:372`, `:378`, `:394`, `:414`, `:420`, `:438`, `:444`, `:459`, `:465`, `:481`), i.e. the majority of equation sections carry no `file:line` at all.
- **code_evidence**: `modules/29_cropland/detail_apr24/equations.gms:11-123`; `detail_apr24/declarations.gms:49-64`; plus every `code_evidence` line in F1-F19.
- **why_it_matters**: This banner is why M29 went ~20 months and one prior audit without these defects surfacing. It tells the next reader — and the next auditor — that the file is settled. The specific harm is asymmetric: the banner is most reassuring exactly where the doc is weakest, because the verification that *was* performed (equation formulas, which are clean) is the part that generalizes least to the parts that weren't (presolve bounds, macros, interface sets). Recommend the banner be replaced with a scoped statement of **what was verified, when, and against which commit** — e.g. "16/16 equation formulas verified against `equations.gms` @ `<sha>`; presolve bounds and cross-module interface sets NOT verified."
- **confidence**: high

---

### F15: "Changes Since Last Verification: None (stable)" — five files changed, and the doc demonstrably post-dates its own verification stamp

- **severity**: Major
- **self_named_class**: `metadata-footer-decoupled-from-body` — a staleness footer that is not merely stale but **provably inconsistent with the body it stamps**, making it worse than no footer
- **fits_existing_taxonomy**: "stale name in a metadata footer" exists as a *Minor* class. This is not that. The footer makes an affirmative falsifiable claim ("None (stable)") that is false, and the body proves the footer wrong — so the footer cannot be repaired by re-dating it; the recorded process didn't happen as described. I'd separate `metadata-footer-decoupled-from-body` from ordinary footer staleness.
- **doc_location**: `modules/module_29.md:1108-1111`
- **doc_says**:
  > **Last Verified**: 2025-10-13
  > **Changes Since Last Verification**: None (stable)
- **code_says**: Since 2025-10-13, **four commits touched `modules/29_cropland/`**, changing five files (most recent 2026-03-21, ~9 months before this audit):
  ```
  896a9b728 2026-03-21  Address review comments: cost regionalization, naming conventions…
  4f4107f2b 2026-03-16  Merge develop - resolve conflicts
  75d7ee167 2026-03-15  Forestry module overhaul…  → detail_apr24/preloop.gms, simple_apr24/not_used.txt
  16fb719e4 2026-03-12  automatic update of realization files → detail_apr24/realization.gms
  da316ed4a 2026-03-12  changelog entries → detail_apr24/scaling.gms
  ```
  Cumulative diffstat vs the doc's stamp date: `detail_apr24/preloop.gms` (4 lines), `detail_apr24/realization.gms` (+1), `detail_apr24/scaling.gms` (**+14, file created**), `simple_apr24/not_used.txt` (4), `simple_apr24/presolve.gms` (1).
  **The footer is self-refuting.** Two independent proofs that the body post-dates 2025-10-13:
  1. `detail_apr24/preloop.gms:46,48` was renamed `pm_carbon_density_secdforest_ac` → `pm_carbon_density_secdforest_ac_uncalib` (and likewise for `plantation`) on **2026-03-15**. The doc uses the **`_uncalib` names** throughout (`:642`, `:650`, `:849`, `:902`) — i.e. it reflects post-rename code.
  2. `detail_apr24/scaling.gms` **did not exist** on 2025-10-13 (created 2026-03-12, +14 lines). The doc's Scaling section (`:776-780`) describes it and correctly states all its statements are commented out.
  So the body was verified against code from **at least 2026-03-15**, while the footer claims 2025-10-13 and asserts nothing changed in between. Separately, the round brief states M29 was audited 2026-05-24 — a date the footer does not reflect either.
- **code_evidence**: `git log --since=2025-10-13 --name-only -- modules/29_cropland/`; `git diff <pre-2025-10-13-sha> HEAD -- modules/29_cropland/detail_apr24/preloop.gms` (shows the `_uncalib` rename); `git log -1 --format='%ai' -- modules/29_cropland/` → `2026-03-21`; `modules/29_cropland/detail_apr24/scaling.gms:1-14`; doc `:642,650,776-780,849,902`.
- **why_it_matters**: The footer is the input to the doc's own staleness badge (AGENT.md Step 1b) and to `/sync` triage. "None (stable)" tells a maintainer that M29 needs no review, which is how a high-centrality module accumulates 19 defects across 20 months. Worse than the staleness: because the footer is provably wrong *in the direction of reassurance*, it cannot be trusted as a lower bound either — a reader cannot infer "verified at least as of 2025-10-13", because the recorded verification evidently didn't happen on that date or in that form.
- **confidence**: high

---

### F16: `p29_avl_cropland` calculation cited at `presolve.gms:32`; it is at `presolve.gms:35`, and line 32 is a different assignment

- **severity**: Minor
- **self_named_class**: `citation-lands-on-neighbouring-statement`
- **fits_existing_taxonomy**: yes (citation drift). Recorded at Minor rather than Major because the doc **quotes the correct code**, so the drift is recoverable in seconds.
- **doc_location**: `modules/module_29.md:117`
- **doc_says**: "**Available Cropland Calculation** (`presolve.gms:32`)" followed by a correct quote of `p29_avl_cropland(t,j) = f29_avl_cropland(j,"%c29_marginal_land%") * (1 - p29_snv_shr(t,j));`
- **code_says**: that statement is at **`presolve.gms:35`**. Line 32 is `p29_snv_relocation(t,j)$(p29_snv_relocation(t, j) > p29_max_snv_relocation(t,j)) = p29_max_snv_relocation(t,j);` — the SNV relocation cap, a different assignment to a different parameter.
- **code_evidence**: `modules/29_cropland/detail_apr24/presolve.gms:32` vs `:35`
- **why_it_matters**: Low harm — the quoted code is right and `:35` is three lines away. Recorded because it is the only line-drift I found in an otherwise strong citation set, and it is consistent with the file having gained lines since the doc's stamp (F15).
- **confidence**: high

---

### F17: Input table gives `f29_snv_target_cropland` dimensions as `(j, relocation_target)`; the set is `relocation_target29`

- **severity**: Minor
- **self_named_class**: `set-name-stripped-of-module-suffix`
- **fits_existing_taxonomy**: yes (identifier accuracy). Minor because the intent is unambiguous.
- **doc_location**: `modules/module_29.md:668`
- **doc_says**: `| SNVTargetCropland.cs3 | f29_snv_target_cropland | … | (j, relocation_target) | Mio. ha |`
- **code_says**: the set is `relocation_target29 / SNV20TargetCropland, SNV50TargetCropland /` (`sets.gms:13-14`), and the table is declared `table f29_snv_target_cropland(j,relocation_target29)` (`input.gms:89`). Bare `relocation_target` is not a set in MAgPIE. Note the doc gets the sibling right — it uses `marginal_land29` correctly in the two rows above (`:666-667`) — so this is inconsistency within one table.
- **code_evidence**: `modules/29_cropland/detail_apr24/sets.gms:13-14`; `detail_apr24/input.gms:89`
- **why_it_matters**: A reader grepping `relocation_target` finds it only as a substring of the real set; low harm, but it fails the exact-identifier rule and would break copy-pasted GAMS.
- **confidence**: high

---

### F18: The "Provided by Module 29" table cites `declarations.gms:38-45` as source for a row (`vm_bv`) that M29 does not declare

- **severity**: Minor
- **self_named_class**: `blanket-citation-covering-a-non-member-row` — one line range applied to a whole table, including a row the range cannot support
- **fits_existing_taxonomy**: unsure. It is citation inaccuracy, but the generative mechanism is specific: a *table-level* citation is asserted once and inherited by every row, so a single wrong row is invisible unless you check each row against the range. Related to the DECLARED-POPULATED-READ MANDATE: M29 **populates** two `vm_bv` slices but **declares** none of it.
- **doc_location**: `modules/module_29.md:684`, `:686`
- **doc_says**: table row `| vm_bv | Biodiversity value (crop_fallow, crop_tree) | (j,landcover,potnatveg) | … | Module 44 |`, under `**Source**: declarations.gms:38-45, verified via grep`.
- **code_says**: two errors in one row.
  1. `vm_bv` is **not declared in M29 at all**. `detail_apr24/declarations.gms:37-46` is the positive-variables block and contains `vm_cost_cropland`(:38), `vm_treecover`(:39), `v29_treecover`(:40), `v29_treecover_missing`(:41), `v29_cost_treecover_est`(:42), `v29_cost_treecover_recur`(:43), `vm_fallow`(:44), `v29_fallow_missing`(:45) — no `vm_bv`. It is declared in **M44** (`44_biodiversity/bv_btc_mar21/declarations.gms:19`). M29 only *populates* the `crop_fallow` and `crop_tree` slices (`equations.gms:76-78,101-104`).
  2. The dimension label is wrong: the set is `landcover44`, not `landcover` (`44_biodiversity/bv_btc_mar21/declarations.gms:19` → `vm_bv(j,landcover44,potnatveg)`).
  The row's *substance* — M29 provides the two `vm_bv` slices to M44 — is correct; only the citation and the set label are wrong.
- **code_evidence**: `modules/29_cropland/detail_apr24/declarations.gms:37-46` (read in full); `modules/44_biodiversity/bv_btc_mar21/declarations.gms:19`; `modules/29_cropland/detail_apr24/equations.gms:76-78,101-104`
- **why_it_matters**: Low harm — the attribution is right and per-slice ownership is the correct mental model. Recorded because "verified via grep" on a citation that cannot be verified by grep is exactly the kind of false assurance F14 is about, in miniature.
- **confidence**: high

---

### F19: "Lines Analyzed: 444" — every component line count is wrong (actual 440)

- **severity**: Minor
- **self_named_class**: `arithmetically-consistent-but-empirically-wrong-tally` — the sum is internally correct, which makes the wrong inputs look checked
- **fits_existing_taxonomy**: yes (fabricated count), at the bottom of the severity band.
- **doc_location**: `modules/module_29.md:6`, `:1103`
- **doc_says**:
  > `:6` **Total Lines**: ~124 (equations.gms)
  > `:1103` **Lines Analyzed**: 124 (equations.gms) + 103 (input.gms) + 17 (sets.gms) + 131 (presolve.gms) + 69 (preloop.gms) = 444 lines
- **code_says**: `wc -l` on `detail_apr24/`: equations.gms **123**, input.gms **103** ✅, sets.gms **16**, presolve.gms **130**, preloop.gms **68**. True total **440**. Four of five components are off by exactly 1, and `124+103+17+131+69` does sum to 444 — the arithmetic is right, the measurements are not. (Note `:6` hedges with "~", so only `:1103` is an unhedged false claim.)
- **code_evidence**: `wc -l modules/29_cropland/detail_apr24/*.gms` this session.
- **why_it_matters**: Negligible on its own. Recorded for one reason: the uniform off-by-one across four independent files is not a measurement error, it is the signature of counts produced by **recollection rather than measurement** — the same generative process behind F11's "12 (6/6)" and F14's "80+ citations". As an isolated fact it is Minor; as evidence about how the doc's numbers were produced, it corroborates F14.
- **confidence**: high

---

## Out-of-taxonomy / unclassifiable observations

Recorded individually, not collapsed. These are things I noticed that I could not cleanly call doc defects.

**O1 — The code contradicts itself about `land_snv`, and the doc sided with the correct half.**
`detail_apr24/realization.gms:15-19` says the SNV option reserves cropland *"for other land cover classes, **including grassland, forest, and other land**"*. But `input.gms:70` defines `land_snv(land) / secdforest, other /` — **no grassland, no primforest**. The doc's Limitation #6 (`:1044-1047`) correctly states secdforest+other only. So the doc is **right and the code's own prose is wrong**. Not a doc defect — arguably a doc success. Flagging because: (a) it's an upstream MAgPIE documentation bug worth reporting to the module authors; (b) a future auditor who "verifies" the doc against `realization.gms` prose rather than `input.gms` would score Limitation #6 as a false finding. This is a case where the naive source-of-truth (the realization's own `@description`) is the wrong one.

**O2 — `simple_apr24` hard-codes sigmoidal fading; `s29_fader_functional_form` exists only in `detail_apr24`.**
`simple_apr24/preloop.gms` calls `m_sigmoid_time_interpol(...)` unconditionally with no `if (s29_fader_functional_form = ...)` branch, and `simple_apr24/input.gms` (73 lines) does not declare the scalar. The doc's Algorithm 1 (`:487-512`) presents the linear/sigmoid switch without realization scope. Not scored as a defect: the doc is explicitly a `detail_apr24` doc and the claim is true there. Recording it because it is a *latent* realization-blend risk — if the config table at `:727` is ever read as module-wide (it is titled "Core Switches", not "detail_apr24 Core Switches"), someone will set `s29_fader_functional_form <- 1` under `simple_apr24` and get a silently ignored switch. Exactly the class F4 belongs to, but not yet realized as an error.

**O3 — `pcm_land` is read by M29 but appears in no dependency list in the doc.**
`detail_apr24/presolve.gms:29` and `:72` both read `pcm_land(j,"crop")`, and it is load-bearing: it is the base for the SNV relocation cap and the denominator of `pc29_treecover_share` (which gates `s29_treecover_keep`). The doc's "Used by Module 29" table (`:690-701`) lists `vm_land` and the dependency list (`:903`) mentions `pm_land_hist`, but `pcm_land` appears nowhere. Not scored separately because it partly overlaps F9's theme and because `pcm_land` is a core carry-forward parameter rather than a conventional module interface — I was genuinely unsure whether the doc's interface tables are *supposed* to cover `pcm_*`. Flagging the ambiguity rather than resolving it. Note the doc's Algorithm 5 correctly uses `pm_land_hist` for *preloop* initialization — the `pcm_land` reads are in *presolve* and are a different code path the doc doesn't cover.

**O4 — Doc's "Two Above-Ground Carbon Pools" gloss is right about the set, arguably misleading about the content.**
`:843-845` says `vegc` = "Crops (annual, negligible stocks)" and `litc` = "Crop residues (small pool)". The set membership is correct (`ag_pools(c_pools) / vegc, litc /`). But in `detail_apr24`, `vegc` also carries **tree-cover** carbon via `m_carbon_stock_ac` — which is emphatically not negligible and is the entire point of the realization. The doc covers tree-cover carbon two bullets later (`:848-851`), so it is not *wrong*, just sequenced so that a skimmer reads "negligible" and stops. Under the default config the "negligible" gloss is actually accurate (F13 — tree cover is 0), which makes this either a defect or a correct-at-defaults statement depending on which framing you accept. I could not decide; recording rather than forcing it into a tier.

**O5 — `q29_treecover_est` is declared over `(j,ac)` but defined over `(j,ac_est)`.**
`declarations.gms:64` declares `q29_treecover_est(j,ac)`; `equations.gms:122` defines `q29_treecover_est(j2,ac_est)`. This is legal, idiomatic GAMS (declare over the full set, define over the dynamic subset) and the doc quotes the *definition* correctly at `:467`. Not a doc defect. Recording it because the doc's §16 gives no hint that `ac_est` is a **dynamic** subset whose cardinality depends on timestep length — which is the whole reason `card(ac_est2)` appears in the equation. The doc's example at `:476-477` conveys this by illustration, so the information is present; the mechanism (dynamic set) is not named.

**O6 — Meta-observation on where the defects clustered, offered as a finding about the audit instrument rather than the doc.**
All 16 equation formulas and all ~20 config defaults are **correct**, and every one of the ~30 `file:line` citations into *other* modules that I spot-checked resolved to the right statement (I verified 11 of them individually). The defects concentrate in exactly four places: **(a)** presolve `.fx`/`.up`/`.lo` bounds (F6, F7), **(b)** macro-expansion semantics (F2, F3), **(c)** interface/consumer *sets* as opposed to individual interface *rows* (F9, F12), and **(d)** the doc's own self-description (F14, F15, F19, F11). Categories (a) and (b) share a property worth naming: **they are one indirection away from the file the doc cites.** The doc cites `equations.gms` and is correct about `equations.gms`; it is wrong about what `presolve.gms` does to the variables in those equations, and wrong about what `core/macros.gms` expands to inside them. Category (c) shares a different property: individual rows are right, the set is wrong — an error that only exists at the aggregate level and cannot be found by checking rows. If a prior single-pass audit read `equations.gms` + `declarations.gms` + `input.gms` and scored per-claim, it would have found **zero** of the Critical findings here and would have been justified in writing the `:1097` banner. That is a hypothesis about the prior 2026-05-24 audit's method, not a verified account of it — but it predicts the observed defect distribution well, and it argues that the highest-yield next lens is "read presolve for bounds, and expand every macro."

---

## Coverage honesty

What I did **not** check, and why:

1. **Input data file contents.** `avl_cropland.cs3`, `avl_cropland_iso.cs3`, `SNVTargetCropland.cs3`, `CroplandTreecover.cs2` and the `_0.5.mz` variants were not parsed. I verified the `table`/`parameter` declarations that read them (`input.gms:75-103`) and their dimension sets, **not** the data. So the doc's units ("Mio. ha") and vintage claims ("2015" for treecover, "2019" for SNV targets) are verified only against the **declaration text** (`input.gms:89,97`), not against the files. Limitation #10's "2019 Copernicus data" is therefore 🟡 documented-in-code, not 🟢 data-verified.

2. **F8's numerical core is unverified.** I verified that `preloop.gms:43-44`'s comment says both growth curves converge to LPJmL natural vegetation, and that M29 merely copies the arrays from M52 (`52_carbon/normal_dec17/start.gms:43-44`). I did **not** inspect the numerical content of `pm_carbon_density_plantation_ac_uncalib` vs `pm_carbon_density_secdforest_ac_uncalib` — they originate in M52 from LPJmL inputs I did not parse. If plantation genuinely plateaus lower, the doc's claim is accidentally true (still unsupported by anything in M29, still contradicted by the authoring comment). This is the one finding whose confidence I would most want a second pass on; it is the reason F8 is medium-high rather than high.

3. **No model was run.** Every behavioural claim — most importantly F13's "fallow and tree cover are identically zero under defaults" and F5's "the run solves and silently pays the penalty" — is derived **algebraically** from bounds, equations, and defaults read this session. F13's fallow half is airtight (`vm_fallow` positive, `.lo=0`, `=l= vm_land*0` ⇒ 0). F13's **tree-cover half rests on a dominance argument**: planting costs money, consumes cropland, and yields no offsetting benefit *inside M29*, so the optimizer sets `ac_est` to 0. I checked M29's own equations for a benefit channel and found none. I did **not** exhaustively rule out an *external* incentive reaching `v29_treecover` through `vm_treecover` → M22/M59 (e.g. a conservation or SOM pathway that makes tree cover pay under some non-default config). Under `config/default.cfg` I believe the dominance holds; I did not verify it against a GDX. Flagged as reasoning, not measurement.

4. **`cross_module/*.md` targets not verified.** module_29.md points at `land_balance_conservation.md` §5.2, `carbon_balance_conservation.md` §3.1, `nitrogen_food_balance.md` Part 1 §1.2 / Part 2, `circular_dependency_resolution.md` §3, and `modification_safety_guide.md`. I did **not** open these, so I cannot say whether those sections exist, whether their numbering is current, or — importantly — whether **F1's phantom Cycle C29 and F10's malformed land-balance invariant have propagated into `circular_dependency_resolution.md` and `land_balance_conservation.md`**. Given that F11 shows the M29↔`Module_Dependencies.md` link is already drifting, I'd treat cross-doc propagation of F1 and F10 as **likely and unchecked**. The single exception: I *did* verify `core_docs/Module_Dependencies.md:25,29-39`, because F11 quotes a number from it.

5. **Consumer greps are broad but not exhaustive over all forms.** For `vm_fallow`, `vm_treecover`, `vm_cost_cropland`, `vm_bv`, `vm_carbon_stock`, `pm_avl_cropland_iso` I grepped `name[(.]`, catching both equation form `vm_x(` and solution form `vm_x.l/.lo/.up/.m`, and ran positive controls. I did **not** cover: (a) macro-mediated reads where the variable is passed as a bare macro argument with no adjacent `(` or `.` — note `58_peatland/v2/equations.gms:23` does exactly this with `m58_LandMerge(vm_land,vm_land_forestry,"j2")`, so this form demonstrably exists in MAgPIE and my pattern would miss an analogous `vm_treecover`/`vm_fallow` case; (b) reads from `.R` post-processing or `magpie4`. So F9's "true outward set ≈ 11 modules" is a **lower bound**. That direction is safe for F9's conclusion (the doc undercounts, and more consumers only strengthen it) but means I cannot certify the set is complete.

6. **Prior-audit provenance not examined.** The brief states M29 was audited once, 2026-05-24. I did not open `audit/validation_rounds.json` or any prior round artifact — deliberately, to keep this pass bottom-up and avoid inheriting the prior round's frame. O6's hypothesis about *why* the prior audit missed these is therefore an inference from the defect distribution, explicitly **not** a verified account of that audit's method.

7. **`postsolve.gms` read only in part.** I read `detail_apr24/postsolve.gms:1-20` and confirmed the load-bearing line `pc29_treecover(j,ac) = v29_treecover.l(j,ac);` at `:8` (which underpins F6). The remaining ~88 lines are R-section output boilerplate (`ov*` assignments); I scanned rather than verified them line-by-line. The doc makes no claims about postsolve, so I judged the residual risk negligible — but it is unverified.

8. **Not checked at all**: `simple_apr24/not_used.txt`, `simple_apr24/postsolve.gms`, `simple_apr24/sets.gms`, `input/files`. The doc makes no claims about these.
