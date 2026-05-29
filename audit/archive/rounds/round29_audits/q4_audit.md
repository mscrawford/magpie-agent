# Audit Report: Q4 (Highest-centrality / riskiest modules; vm_land consumer attribution)

**Round**: R29
**Auditor worktree**: `/tmp/magpie-develop-r29/` @ `ee98739fd57267c0f681a418e1d1b0513f5cb22d` (Merge PR #887)
**Answer audited**: `audit/archive/rounds/round29_answers/q4_answer.md`

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 8/10

The answer's spine is strong: the interface variable (`vm_land(j,land)`), the controlling equation (`q10_land_area`), and **every** primary consumer-equation attribution (`q29_cropland`, `q31_prod`, `q35_land_secdforest`, `q35_land_other`, `q32_land`, `q50_nr_inputs_pasture`) were verified to read `vm_land` with the stated land type at the cited file:line, in the **default** realization of each module. The core 10-module direct-consumer list is empirically exact. Two defects pull it off a 9-10: (1) a false consumer attribution of M71 + M80 ("via land-consistency constraints"), and (2) a wrong-provenance claim for `pm_land_start` ("initialized from vm_land"). A latent doc bug in `module_10.md` (wrong vm_land consumer set) is the upstream source of defect (1) and is recorded separately per §1.5.

---

### Verified Claims (correct)

**Centrality / hub framing (§1):**
- Centrality table M11=28, M10=17 (15 out / 2 in), M56=16, M17=14 — matches `core_docs/Module_Dependencies.md:31-37` exactly. ✓ (Selective "four hubs" framing omits M32@16 and M09@14, but the cited numbers are accurate; defensible editorial choice, not a bug.)
- `vm_emission_costs(i)` declared in M56 — `modules/56_ghg_policy/price_aug22/declarations.gms:39`. ✓
- `vm_prod_reg(i,kall)` and equation `q17_prod_reg` — declared `17_production/flexreg_apr16/declarations.gms:10`; equation `equations.gms:10`. Index `(i,kall)` correct. ✓ M17 sole realization `flexreg_apr16`. ✓

**Interface variable + controlling equation (§2):**
- M10 sole realization `landmatrix_dec18`. ✓
- `vm_land(j,land)` is a positive variable, units mio. ha. ✓ Declaration is at `declarations.gms:19` (answer cites `:14` — see Bug Q4-B3, citation drift to the `variables`/`positive variables` header region).
- `land` set = `crop, past, forestry, primforest, secdforest, urban, other` (7 types) — `core/sets.gms:250-251`. ✓ (answer lists all 7 correctly.)
- `q10_land_area(j2) .. sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));` — `10_land/landmatrix_dec18/equations.gms:13-15`. Verbatim match, strict `=e=`. ✓
- `pcm_land(j,land) = vm_land.l(j,land);` at `postsolve.gms:9`. ✓

**Direct consumer list (§2.1):** "10 direct consuming modules: 22, 29, 30, 31, 32, 34, 35, 50, 58, 59" — EMPIRICALLY EXACT. `find modules -name '*.gms' -exec grep -l 'vm_land\b' {} \; | awk -F/ '{print $2}' | sort -u | grep -v '^10_land$'` returns precisely {22, 29, 30, 31, 32, 34, 35, 50, 58, 59}. Matches `modification_safety_guide.md:54-55`. ✓ Per-module spot checks: M58=1 file, M30=2, M34=3 all reference `vm_land`. ✓

**Primary consumer equations (§3) — all directly read vm_land at cited line, default realizations:**
- §3.1 `q29_cropland` — `29_cropland/detail_apr24/equations.gms:11-12`: `vm_land(j2,"crop") =e= ...`. ✓ Default `detail_apr24` (config:795 `def = detail_apr24`). ✓ `q29_avl_cropland` at :22-23 bounds `vm_land(j2,"crop")`. ✓ `q29_land_snv` exists (`equations.gms:49`). ✓ Cascade-into-q10 claim correct (q10 sums all land incl. crop).
- §3.2 `q31_prod` — `31_past/endo_jun13/equations.gms:16-18`: `vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(...)`. ✓ Default `endo_jun13` (config:969). ✓ `vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type))` at `presolve.gms:9`. ✓
- §3.3 `q35_land_secdforest` (`equations.gms:11`) + `q35_land_other` (`equations.gms:13`) — `35_natveg/pot_forest_may24/`, both read `vm_land(j2,"secdforest")` / `vm_land(j2,"other")` directly. ✓ Default `pot_forest_may24` (config:1135). ✓ primforest one-way-decline: `presolve.gms:143-145` is the explanatory comment for that mechanism (bound code follows); citation lands on the right mechanism. ✓ (minor imprecision, comment vs code, not a bug.)
- §3.4 `q50_nr_inputs_pasture` — `50_nr_soil_budget/macceff_aug22/equations.gms:74-80`: term `sum((cell(i2,j2)), vm_land(j2,"past")) * sum(ct,f50_nr_fixation_rates_pasture(ct,i2))` at line 79. ✓ Default+sole `macceff_aug22` (config:1479). ✓ N-fixation interpretation correct.
- §3.5 `q32_land` — `32_forestry/dynamic_may24/equations.gms:55-56`: `vm_land(j2,"forestry") =e= sum((type32,ac), v32_land(j2,type32,ac));`. ✓ Default+sole `dynamic_may24` (config:976). ✓
- §3.6 M22 `pm_land_conservation(t,j,land,consv_type)` — index corroborated by consumption sites (M31 presolve.gms:9 `pm_land_conservation(t,j,"past",consv_type)`; M35 `pm_land_conservation(ct,j2,land_natveg,"protect")`). M22 has no equations. ✓
- §3.7 M59 (`cellpool_jan23`, default — config:1916) reads BOTH `vm_land` (equations.gms:33, 63) AND `vm_landexpansion` (equations.gms:91, `q59_nr_som_fertilizer2`). ✓ Outputs `vm_cost_scm` (declarations.gms:41) and `vm_nr_som` (declarations.gms:45) exist. ✓ (The answer was appropriately humble — flagged "no specific consuming equation cited" in its Not-in-Docs section — but the underlying both-variables claim is correct and now verified.)

**Self-flagged limitations (§"Not in Docs"):** The answer's note that the 10-vs-15 discrepancy is the direct-consumer vs any-interface-variable distinction is CORRECT and matches `modification_safety_guide.md:54-58`. Credit for surfacing this.

---

### Bugs Found

#### Bug Q4-B1 — False consumer attribution of M71 + M80
- **Severity**: 🟠 Major
- **Class**: 4 (Conceptual pseudo-code / false attribution) — Pattern D false consumer attribution
- **Trigger** (§1 Major): "Recommendation/claim that contradicts maintainer practice / code without an anchor" + fabricated mechanism. (Considered Critical via R20 consumer-set anchor, but tie-breaker pulls down: the load-bearing 10-module set is correct and the misattribution is confined to a hedged parenthetical, so harm is bounded — a reader gets the right blast radius and only over-includes two modules.)
- **Claim in answer** (§2.1): "...10 direct consuming modules ... 22, 29, 30, 31, 32, 34, 35, 50, 58, 59 **(plus 71 and 80 via land-consistency constraints)**." (§4 cascade does not repeat it, but §2.1 states it as fact.)
- **Reality in code**:
  - **M71** (`71_disagg_lvst`): **0 of 22** `.gms` files reference `vm_land` (verified: `find modules/71_disagg_lvst -name '*.gms' -exec grep -l vm_land {} \;` → empty; count 0). M71 does not consume `vm_land` at all.
  - **M80** (`80_optimization`): the **default** realization `nlp_apr17` (config:2282 `def = nlp_apr17`) has **0** `vm_land` references. Only the **non-default** `lp_nlp_apr17/solve.gms` references it (4 hits — variable fixing for the two-stage LP→NLP solve loop), and `module.gms:15` mentions only `vm_landdiff` in a comment. There is no "land-consistency constraint" in M80 (M80 has no equations.gms).
  - The phrase "via land-consistency constraints" is a **fabricated mechanism** for both: M71 is livestock disaggregation; M80 is the optimization driver.
- **File evidence**: `modules/71_disagg_lvst/` (0/22 gms with vm_land); `modules/80_optimization/nlp_apr17/solve.gms` (0 hits, default); `modules/80_optimization/lp_nlp_apr17/solve.gms` (4 hits, non-default); `config/default.cfg:2282`.
- **Root cause**: `answerer_pulled_wrong_doc` — the answer cited BOTH `modification_safety_guide.md:54-55` (correct, lists exactly 10, excludes 71/80) AND `module_10.md:315-318` (wrong, includes 71/80). It reconciled the conflict by appending 71/80 as a parenthetical instead of trusting the empirically-recomputed safety-guide list. The upstream doc defect is recorded as Q4-D1.
- **Anchor reference**: R20 `pm_carbon_density_ac` consumer-set anchor (wrong consumer set → user misses/over-includes modules in a refactor). Downgraded to Major per tie-breaker because the correct 10-set is present and the error is a hedged add-on.

#### Bug Q4-B2 — Wrong provenance for `pm_land_start` ("initialized from vm_land")
- **Severity**: 🟠 Major
- **Class**: 4 (Conceptual pseudo-code / misstated mechanism) + parameterization-vs-source confusion
- **Trigger** (§1 Major): "claim is wrong in a way that misleads about behavior, but won't directly cause damaging action."
- **Claim in answer** (§3.5): "Module 32 also reads `pm_land_start(j,land)` (initialized from `vm_land` in `start.gms:8`), so initial plantation establishment calculations would also break."
- **Reality in code**:
  - `pm_land_start` is initialized from an **input file**, NOT from `vm_land`: `10_land/landmatrix_dec18/start.gms:8` → `pm_land_start(j,land) = f10_land("y1995",j,land);`. (`f10_land` is read-in land area; the link to `vm_land` is the reverse — `pcm_land` is seeded from `pm_land_start` at start.gms:11.)
  - The `start.gms:8` citation is **Module 10's** start.gms. **Module 32's `dynamic_may24` directory has no `start.gms` file at all.** M32 reads `pm_land_start` in `preloop.gms:162-171` (e.g., `pm_land_start(j,"forestry") * ...`), not in any start.gms.
  - So the sentence misattributes both the provenance (input data, not vm_land) and the read location (M10 start.gms, not M32).
- **File evidence**: `modules/10_land/landmatrix_dec18/start.gms:8` (`= f10_land(...)`), `:11` (`pcm_land = pm_land_start`); `modules/32_forestry/dynamic_may24/preloop.gms:162-171` (actual M32 reads); M32 dir has no start.gms.
- **Root cause**: `confused_initialization_source` — answerer asserted a vm_land→pm_land_start initialization that runs the wrong direction and cited the wrong module's file. Violates the AGENT.md "uses data about X ≠ models X" / provenance rule. Secondary supporting claim only (the primary §3.5 attribution `q32_land` reads `vm_land` is correct), hence Major not Critical.

#### Bug Q4-B3 — `vm_land` declaration citation off by 5 lines
- **Severity**: 🟡 Minor
- **Class**: 10 (Stale/imprecise file:line citation)
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things."
- **Claim in answer** (§2.1): "Declaration: `modules/10_land/landmatrix_dec18/declarations.gms:14`".
- **Reality in code**: `vm_land(j,land)` is declared at `declarations.gms:19` (inside the `positive variables` block, lines 18-24). Line 14 is the `variables` keyword header (which declares only `vm_landdiff`). A careful reader landing on :14 sees the variables block start and the correct var two lines down — adjacent, same topic.
- **File evidence**: `modules/10_land/landmatrix_dec18/declarations.gms:14` (`variables`), `:19` (`vm_land(j,land)  ... (mio. ha)`).
- **Root cause**: `citation_to_block_header` — cited the block header line instead of the variable line.

---

### Latent Doc Bugs (§1.5 — recorded independent of answer score; fix this session)

#### Doc bug Q4-D1 — `module_10.md` lists a wrong/inflated `vm_land` consumer set
- **Severity**: 🔴 Critical (by future-reader harm, per R20 anchor)
- **Root cause**: `doc_error` (this round the answer was PARTIALLY beaten by the doc — it correctly cited the right list from `modification_safety_guide.md` but then re-injected the wrong modules from `module_10.md` into a parenthetical, producing Q4-B1). Not purely `doc_error_answerer_beat_it` because the bad doc DID leak into the answer.
- **Doc location & claim**:
  - `modules/module_10.md:312-313` — "provides to" table rows `71_disagg_lvst | vm_land (1)` and `80_optimization | vm_land (1)`.
  - `modules/module_10.md:315-318` — "**Critical Consumers of `vm_land`** (11 modules total)" list includes `11_costs, 14_yields, 39_landconversion, 71_disagg_lvst, 80_optimization` alongside the genuine consumers. (It also says "11 modules total" but enumerates ~16 — internally inconsistent.)
- **Reality in code**: exactly **10** modules reference `vm_land` directly: 22, 29, 30, 31, 32, 34, 35, 50, 58, 59. Verified non-consumers: **11_costs = 0** gms files, **14_yields = 0**, **39_landconversion = 0**, **71_disagg_lvst = 0**, **80_optimization = 0 in default `nlp_apr17`** (non-default lp_nlp only). These modules consume OTHER M10 interface vars (`vm_landexpansion`, `pcm_land`, `vm_landdiff`, `pm_land_start/hist`) — not `vm_land`.
- **Contradicting correct doc**: `cross_module/modification_safety_guide.md:54-58` draws the correct distinction (10 direct vm_land consumers; broader 18-module union for any M10 interface var) and was recomputed 2026-05-23 (R3). `module_10.md` was not updated to match and conflates the two sets.
- **Fix**: in `module_10.md`, correct the "Critical Consumers of `vm_land`" block (:315-318) to the empirically-verified 10-module set and relabel the broader list as "modules touched by any Module 10 interface variable" (mirroring `modification_safety_guide.md:54-58`); remove the `vm_land (1)` attribution from the `71_disagg_lvst` and `80_optimization` provides-to rows (:312-313) or re-tag them to the actual interface variable they consume. Cross-link to `modification_safety_guide.md:52` recompute command so the two docs stay in sync.
- **Anchor reference**: R20 `pm_carbon_density_ac` (wrong consumer set is Critical by future-reader harm) + the §1.5 G2-carbon-stock immutable anchor (a wrong producer/consumer list left in a module doc silently regresses a future round).

---

### Mechanical checks
- **M1** (file:line present): PASS — dozens of `modules/XX/realization/file.gms:NN` citations.
- **M2** (active realization stated): PASS — M10 noted "only realization"; default realizations correct for all deep-dived consumers (29/detail_apr24, 31/endo_jun13, 32/dynamic_may24, 35/pot_forest_may24, 50/macceff_aug22, 59/cellpool_jan23 all verified as defaults). NOTE: M80 realization-dependence is exactly what Q4-B1 missed — the (false) 80-consumer claim is also realization-blind.
- **M3** (variable prefixes valid): PASS — vm_land, pcm_land, pm_land_start, vm_emission_costs, vm_prod_reg, vm_cost_scm, vm_nr_som all valid prefixes.
- **M4** (epistemic badges): minor — closing "Documentation Relied Upon" + "Not in Docs" present; inline 🟢/🟡 badges sparse but source attribution is per-section. Not scored as a bug (Informational at most).
- **M5/M6**: PASS — closing source statement present ("Documentation Relied Upon").

### Missing nuances
- §4 cascade diagram omits M58 (peatland) and M30 (croparea) and M34 (urban), which ARE in the verified 10-consumer set. Not a bug (the answer's §2.1 listed all 10; the cascade just doesn't expand every one), but the diagram is less complete than the list.
- The answer never states which M80 realization it means — consistent with the fact that the 80-claim is spurious.

### Summary
Strong, well-cited answer on the load-bearing content: the interface variable (`vm_land`), the conservation equation (`q10_land_area`), and all six primary consumer equations (`q29_cropland`, `q31_prod`, `q35_land_secdforest`, `q35_land_other`, `q32_land`, `q50_nr_inputs_pasture`) were verified verbatim at the cited file:line in the correct default realization of each module — i.e., the question's core ask (real consumer attribution) is correct. The 10-module direct-consumer set is empirically exact.

Defects:
- **B1 (Major)** — false consumer attribution of M71 (0 vm_land refs) and M80 (0 in default realization; non-default lp_nlp only), with a fabricated "land-consistency constraints" mechanism. Hedged parenthetical; the correct 10-set dominates, so harm is bounded (over-inclusion, not omission) → Major, not Critical.
- **B2 (Minor)** — wrong provenance for `pm_land_start` ("initialized from vm_land in start.gms:8"; actually from input `f10_land` in M10's start.gms, and M32 reads it in preloop.gms not start.gms). Secondary supporting claim; primary §3.5 attribution is correct → tie-breaker to Minor.
- **B3 (Minor)** — `vm_land` declaration cited at declarations.gms:14 (block header) vs actual :19.

Severity-weighted (§4, binding): 1·Major(2) + 2·Minor(1+1) = 4. Score = 10 − 4 = **6**.

Latent doc bug **Q4-D1 (Critical by future-reader harm)** — `module_10.md:312-318` lists 11/14/39/71/80 as vm_land consumers; only 10 modules consume it directly. Does NOT lower the answer score (§1.5) but MUST be fixed this session.

**Final score: 6/10 — MOSTLY ACCURATE (lower band).**
</content>
</invoke>
