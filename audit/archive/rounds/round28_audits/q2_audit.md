# Audit Report: Q2 (Land-conversion costs in the DEFAULT configuration — Module 39 → 10 → 11)

**Round**: 28
**Verification worktree**: `/tmp/magpie-develop-r28/` @ `ee98739fd`
**Answer file**: `audit/archive/rounds/round28_answers/q2_answer.md`

---

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 7/10

The answer is structurally excellent: it correctly states the default realizations of all three modules, traces the full cost-propagation chain (vm_lu_transitions → vm_landexpansion/reduction → vm_cost_landcon → q11_cost_reg → vm_cost_glo), and cleanly distinguishes M39's `vm_cost_landcon` from M10's `vm_cost_land_transition`. Every M10 and M11 equation it quotes is **verbatim-faithful** to the code, and every M10/M11 file:line citation is exact. The single material deduction is the q39_cost_landcon formula rendering, which drops the GAMS cell-to-region mapping sums (inherited from a doc simplification); plus one minor over-generalization about a non-default switch.

---

### Verified Claims (correct):

- **M39 default realization = `calib`**: confirmed `config/default.cfg:1267` `cfg$gms$landconversion <- "calib"`. Only one realization dir besides `input/` (`modules/39_landconversion/calib/`). ✓
- **M10 = `landmatrix_dec18`**: `config/default.cfg:232`. ✓
- **M11 = `default`**: `config/default.cfg:236`. ✓
- **`vm_cost_landcon(j,land)` declared at M39 `declarations.gms:13`**: confirmed (line 13, `variables` block). ✓ Described as the interface cost variable to M11 — correct.
- **`q39_cost_landcon(j2,land)` at `equations.gms:12-15`**: confirmed the equation spans exactly lines 12-15. ✓
- **Operands of q39 formula** (expansion×establish − reduction×reward)×annuity, sign convention (expansion +, reduction −, net can be negative): all faithful to `equations.gms:12-15`. ✓
- **`i39_cost_establish` / `i39_reward_reduction` / `i39_calib` declared at `declarations.gms:17/18/19`**: confirmed exactly. ✓
- **Cropland calibration applied in `presolve.gms:12-13`**: confirmed (line 12 cost, line 13 reward). ✓
- **Pasture/forestry/urban fixed global costs in `presolve.gms:14-16`**: confirmed. ✓
- **`s39_cost_establish_crop = 12300` (`input.gms:9`), `s39_reward_crop_reduction = 7380` (`input.gms:10`, = 60% of 12300), `s39_ignore_calib = 0` (`input.gms:14`)**: all confirmed exactly. Pasture 9840, forestry 1230, urban 12300 also confirmed (`input.gms:11-13`). ✓
- **Reduction reward condition** (cropland only, regions with 1995-2015 decline AND calib>1): grounded in `presolve.gms:8-10` source comment. ✓
- **q10_landexpansion as off-diagonal inflow sum** (`equations.gms:30-33`): quoted **verbatim-correct**, including `$(not sameas(land_from,land_to))`. ✓
- **q10_landreduction as off-diagonal outflow sum** (`equations.gms:35-38`): **verbatim-correct**. ✓
- **q10_land_area conservation** (`equations.gms:13-15`): `sum(land,vm_land)=e=sum(land,pcm_land)`; "total land per cell conserved strictly" — correct. ✓
- **q10_transition_to (19-21) = inflows = current area (vm_land); q10_transition_from (23-25) = outflows = previous area (pcm_land)**: descriptions match code exactly. ✓
- **vm_lu_transitions is 7×7 (49/cell)**: `land` set = {crop,past,forestry,primforest,secdforest,urban,other} = 7 members (`core/sets.gms:250-251`). ✓
- **q10_cost (`equations.gms:42-44`) = 1 USD/ha penalty on gross change**: quoted verbatim; `*1` on (expansion+reduction) summed over land. ✓
- **vm_cost_land_transition enters M11 separately at `equations.gms:41`**: confirmed `+ sum(cell(i2,j2), vm_cost_land_transition(j2))` at line 41. ✓ Distinction from vm_cost_landcon is correct and well-articulated.
- **M39 term in q11_cost_reg at `equations.gms:20`**: `+ sum((cell(i2,j2),land), vm_cost_landcon(j2,land))` — **verbatim-correct**, exact line. ✓
- **q11_cost_glo (`equations.gms:10`)**: `vm_cost_glo =e= sum(i2, v11_cost_reg(i2))` — verbatim-correct. ✓
- **vm_cost_glo is the minimized objective**: confirmed `solve magpie USING nlp MINIMIZING vm_cost_glo` (e.g. `modules/80_optimization/nlp_ipopt/solve.gms:62`). ✓
- **vm_cost_glo / v11_cost_reg declared at M11 `declarations.gms:9/10`**: confirmed. ✓
- **q11_cost_reg at `equations.gms:15-47`**: confirmed. ✓
- **pm_interest from M12, dimensioned (t,i)**: confirmed declared `pm_interest(t_all,i)` at `modules/12_interest_rate/select_apr20/declarations.gms:9`. ✓
- **M11 is a pure aggregator**: q11_cost_reg is a flat sum of cost interface variables — correct. ✓

---

### Bugs Found:

#### Bug Q2-B1 — q39 formula drops the GAMS cell-to-region mapping sums
- **Severity**: Major
- **Class**: 4 (Conceptual pseudo-code) / overlaps 10-12 (the block is attributed to `equations.gms:12-15` but is not the literal content)
- **Trigger** (§1 Major): "Right concept ... but won't directly cause damaging action" + matches the R16 set-sum-rendering anchor (set-based sum re-rendered, value-correct, misleads about how the code reads). NOT Critical: the operands, operation, sign, and annuity are all faithful and the value is identical, so it is not a "fabricated formula."
- **Claim in answer** (lines 70-76, repeated 133-137):
  ```gams
  q39_cost_landcon(j,land) ..
    vm_cost_landcon(j,land) =e=
      (vm_landexpansion(j,land) * i39_cost_establish(i,land)
       - vm_landreduction(j,land) * i39_reward_reduction(i,land))
      * pm_interest(i) / (1 + pm_interest(i))
  ```
- **Reality in code** (`/tmp/magpie-develop-r28/modules/39_landconversion/calib/equations.gms:12-15`):
  ```gams
  q39_cost_landcon(j2,land) .. vm_cost_landcon(j2,land) =e=
    (vm_landexpansion(j2,land)*sum((ct,cell(i2,j2)), i39_cost_establish(ct,i2,land))
    - vm_landreduction(j2,land)*sum((ct,cell(i2,j2)), i39_reward_reduction(ct,i2,land)))
    * sum((cell(i2,j2),ct),pm_interest(ct,i2)/(1+pm_interest(ct,i2)));
  ```
  The parameters `i39_cost_establish(t,i,land)`, `i39_reward_reduction(t,i,land)` and `pm_interest(t,i)` are dimensioned over region `i` and time `t`, but the equation is indexed over cell `j2`. The code uses `sum((ct,cell(i2,j2)), ...)` — a GAMS cell→region+current-timestep lookup idiom — which the answer omits, writing direct `(i,land)`/`(i)` indices. The collapsed form is **numerically equivalent** (each `cell(i2,j2)` selects one region; `ct` is the current-timestep singleton), so the harm is to code-fidelity, not to the economics: a reader cannot copy-paste the block, and a user editing the equation must preserve the cell-mapping sum. The answer's prose (lines 83-85) does correctly flag these as `(t,i)` regional parameters, which mitigates.
- **File evidence**: `modules/39_landconversion/calib/equations.gms:12-15` (worktree).
- **Anchor reference**: R16 — "agent fabricated an expanded `q10_land_area` equation ... Code uses `sum(land, vm_land(j,land))`; agent wrote the enumerated form. → Major (would mislead a reader about how the code reads, but not into a wrong code edit)." This is the same class (set-based sum re-rendered), inverse direction.
- **Root cause**: `doc_error` (inherited). module_39.md presents the identical simplified block — see Latent Doc Bug A. The answerer faithfully reproduced the doc; it did not confabulate.

#### Bug Q2-B2 — "sets all calibration factors to 1" under s39_ignore_calib=1 (reward factor actually → 0)
- **Severity**: Minor (`tier_uncertainty: true` — borderline Informational; kept at Minor because it is a wrong *value* claim, not a style issue)
- **Class**: 13 (parameter value), low end (value under a non-default switch, not a default)
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action or misunderstanding" — the practical takeaway (calibration disabled, uniform costs) is conveyed correctly; the slip is the precise reward-factor value.
- **Claim in answer** (line 103): "Setting it to 1 disables regional variation and sets all calibration factors to 1."
- **Reality in code** (`modules/39_landconversion/calib/preloop.gms:13-16`): when `s39_ignore_calib = 1` (or the input file is empty), `i39_calib(t,i,"cost") = 1` **and** `i39_calib(t,i,"reward") = 0` — the reward factor is set to **0**, not 1. (module_39.md:392 states this correctly; the answer over-generalized.)
- **File evidence**: `modules/39_landconversion/calib/preloop.gms:14-15` (worktree).
- **Anchor reference**: none directly; mild instance of the Minor "wrong detail" tier.
- **Root cause**: `answerer_confabulation` (the doc was correct; the answerer over-generalized). Peripheral to the question (about a non-default testing switch).

---

### Latent Doc Bugs (recorded per §1.5; do NOT lower the answer score):

#### Latent Doc Bug A — module_39.md presents the q39 formula without the cell-mapping sums
- **Severity (by future-reader harm)**: Major
- **Root cause**: `doc_error` (NOT `doc_error_answerer_beat_it` — the answer did **not** beat the doc; it reproduced the same simplification, so this is the source of Bug Q2-B1).
- **Doc lines**: `magpie-agent/modules/module_39.md:96-102` (the ```gams``` block attributed to `equations.gms:12-15`) and the §14.2 restatement at `module_39.md:929-930`.
- **Doc says** (96-102): `... i39_cost_establish(i,land) ... i39_reward_reduction(i,land) ... pm_interest(i) / (1 + pm_interest(i))` — direct-indexed, no `sum((ct,cell(i2,j2)), ...)`.
- **Contradicting code**: `modules/39_landconversion/calib/equations.gms:12-15` wraps each region/time parameter in `sum((ct,cell(i2,j2)), ...)` / `sum((cell(i2,j2),ct), ...)`.
- **Doc fix**: Either (a) reproduce the actual code faithfully with the cell-mapping sums in the ```gams``` block, or (b) keep the simplified block but relabel it explicitly as a "mathematical form / value-equivalent simplification" rather than attributing it as the literal `equations.gms:12-15` content (the doc already has a correctly-labeled "Mathematical Form" at lines 104-109 — the fix is to stop presenting the simplified GAMS block as verbatim file content). Recommended: option (b) plus a one-line note that the code uses the `sum((ct,cell(i2,j2)),...)` j→i lookup idiom.

#### Latent Doc Bug B — module_39.md understates vm_cost_landcon land dimension
- **Severity (by future-reader harm)**: Minor
- **Root cause**: `doc_error` (NOT inherited — the answer correctly wrote `vm_cost_landcon(j,land)` over the full set).
- **Doc line**: `magpie-agent/modules/module_39.md:286` — "Dimensions: [j, land] where land = {crop, past, forestry, urban}".
- **Contradicting code**: `vm_cost_landcon(j,land)` is declared over the full 7-member `land` set (`declarations.gms:13`; `core/sets.gms:250-251`). primforest/secdforest/other simply carry zero establishment cost (`preloop.gms:8` initializes to 0; `presolve.gms:12-16` only overwrites the 4 named types). The variable is defined for all 7 land types, not 4.
- **Doc fix**: Change the dimension note to "land = full 7-member land set; only crop/past/forestry/urban carry a non-zero establishment cost — primforest/secdforest/other have zero cost (initialized in `preloop.gms:8`, never overwritten)."

---

### Missing Nuances (not bugs):

- The answer does not explicitly state that **primforest/secdforest/other have zero conversion cost** (their `i39_cost_establish` stays at the `preloop.gms:8` initialization of 0). The Section-2 table lists only the 4 priced types, which is consistent, but a one-line "the other three land types are uncosted" would have closed the loop on "what transitions trigger costs."
- The "calibration converges to minimum 1.0 by 2050" claim (line 99) is a property of the `f39_calib.csv` **input data** (constructed in preprocessing / recalibration), not enforced in the M39 GAMS code. The answer states it as the doc does; it is not load-bearing for the cost-propagation question, but a parameterization-vs-mechanism caveat would have been more precise.
- M4 mechanical check: the answer carries a single closing 🟡 badge (line 207) but does **not** badge individual substantive claims with 🟢/🟡. Informational only (weight 0); noted for completeness.

---

### Mechanical Checks:
- **M1** (file:line present): PASS — extensive, accurate citations.
- **M2** (active realization stated): PASS — M39 `calib` (default), M10 `landmatrix_dec18`, M11 `default`, all named.
- **M3** (prefixes valid): PASS — vm_/i39_/s39_/pm_/v11_/q-prefixes all valid.
- **M4** (per-claim epistemic badges): FAIL — only one closing 🟡; no per-claim badges. (Informational.)
- **M5** (confidence tier matches depth): PASS — single 🟡 "based on docs" is consistent with a docs-only answer.
- **M6** (closing source statement): PASS — line 207 "Based on module_39.md, module_10.md, module_11.md documentation."

---

### Score Computation:
```
critical = 0, major = 1 (Q2-B1), minor = 1 (Q2-B2), informational = 1 (M4)
raw_severity_weighted = 4·0 + 2·1 + 1·1 + 0·1 = 3
score = max(0, 10 - 3) = 7
```
Latent doc bugs (A Major, B Minor) are recorded in `doc_errors_latent[]` and do not affect the answer score (§1.5). Bug Q2-B1's root cause is the same simplification as Latent Doc Bug A.

### Summary:
A strong, well-organized answer that nails the cross-module spine — default realizations, the off-diagonal-sum derivation of vm_landexpansion/reduction from vm_lu_transitions, the q10 conservation/transition constraints, the M39-vs-M10 cost-variable distinction, and the q11_cost_reg → q11_cost_glo objective path — with verbatim-faithful M10/M11 equation quotes and exact citations throughout. The 3-point deduction is almost entirely a single inherited doc simplification: the q39 formula is presented without the `sum((ct,cell(i2,j2)),...)` cell→region mapping idiom (value-correct, code-infidelity → Major), plus a minor over-generalization of the s39_ignore_calib effect on the reward factor. Both the formula simplification (Latent Doc Bug A, Major by future-reader harm) and the vm_cost_landcon land-dimension understatement (Latent Doc Bug B, Minor) should be fixed in module_39.md this session per §1.5.
