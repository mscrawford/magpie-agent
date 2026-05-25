# Audit Report: Q2 (M80 Default Solver Scalars)

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

The answer correctly identifies the default realization (`nlp_apr17`), correctly enumerates the four input-scalar defaults (`s80_maxiter=30`, `s80_optfile=1`, `s80_secondsolve=0`, `s80_toloptimal=1e-08`), correctly traces the 4-strategy `s80_resolve_option` cycle and resets, and correctly identifies the realization-asymmetry (`s80_resolve_option` only in `nlp_apr17`; `s80_obj_linear` only in `lp_nlp_apr17`). Bugs are a citation-drift duo on `nlp_apr17/declarations.gms` line numbers (off-by-one for both `s80_counter` and `s80_resolve_option`) and an undercount of `s80_secondsolve` injection points in `lp_nlp_apr17`. The line-number bugs trace to a pre-existing doc_error in `module_80.md`, which the answerer trusted rather than re-verifying.

The PHASE 2B GATE PASSED in the structural sense: the answer used `nlp_apr17`-rooted defaults throughout, never pulled defaults from `lp_nlp_apr17/declarations.gms` to describe default behavior. But the gate spirit is also partly **failed**: the gate's premise was that a 2b sweep added a `nlp_apr17` Parameters table; the existing `module_80.md` Parameters table for `nlp_apr17` (lines 309-316) carries the same wrong declarations.gms line numbers that the answer now propagates. The sweep added the table but did not verify its line citations against source.

---

### Mechanical Checks (M1-M6)

| Check | Pass | Notes |
|---|---|---|
| M1 (file:line citations) | ✅ | Multiple `nlp_apr17/...gms:NN` citations present |
| M2 (active realization stated) | ✅ | "default optimization realization is **`nlp_apr17`**" stated up front and verified against default.cfg |
| M3 (variable prefixes valid) | ✅ | All `s80_*`, `p80_*`, `vm_*` prefixes correct |
| M4 (epistemic badges present) | ✅ | 🟡 badges throughout |
| M5 (confidence matches depth) | ⚠️ | All claims tagged 🟡 (documented). Some claims (like the `decisions.gms:14` line for `s80_resolve_option`) appear to have been read from `module_80.md` rather than from source — if source had been re-read this session, the off-by-one would have been caught. Tag is technically correct (citing docs not session-verified source), but the **footer claim** "verified 2026-05-16 against `nlp_apr17/*.gms`" is in tension with the citation drift. |
| M6 (closing source statement) | ✅ | "Based on module_80.md documentation (verified 2026-05-16 against `nlp_apr17/*.gms` and `lp_nlp_apr17/*.gms`)." |

---

### Verified Claims (correct)

- **Active realization**: `cfg$gms$optimization <- "nlp_apr17"` confirmed at `config/default.cfg:2280` ("def = nlp_apr17"). ✓
- **Four input scalars + defaults**: confirmed verbatim against `nlp_apr17/input.gms:8-13`:
  - `s80_maxiter / 30 /` at line 9 ✓
  - `s80_optfile / 1 /` at line 10 ✓
  - `s80_secondsolve / 0 /` at line 11 ✓
  - `s80_toloptimal / 1e-08 /` at line 12 ✓
- **Range `nlp_apr17/input.gms:8-13`**: file actually runs 1-13 with scalars block 8-13. ✓
- **`s80_optfile` mechanism**: `magpie.optfile = s80_optfile` at `nlp_apr17/solve.gms:16`. ✓
- **`s80_secondsolve` mechanism**: `if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );` at `nlp_apr17/solve.gms:36` (answer cites 34-36, line 34 is the preceding solve, line 35 is a comment — close enough as a range). ✓
- **`s80_toloptimal` written to conopt4 optfile**: `put 'Tol_Optimality = ', s80_toloptimal:12:11 /;` at `nlp_apr17/solve.gms:22` (answer says 22-27 — line 22 is the put, 23 is the close, 25-27 is the op2 onecho/offecho; range is loose but acceptable for context). ✓
- **`s80_resolve_option` 4-strategy cycle**: confirmed against `nlp_apr17/solve.gms:48-92` (52-68 are the strategy if/elseif). All four strategies match (CONOPT4 default, CONOPT4 optfile=1, CONOPT4 optfile=2 with relaxed limits, CONOPT3). ✓
- **`s80_resolve_option` reset**: `s80_resolve_option$(s80_resolve_option >= 4) = 0;` at `nlp_apr17/solve.gms:89`. ✓
- **`s80_maxiter` loop termination**: `until (magpie.modelstat <= 2 or s80_counter >= s80_maxiter)` at `nlp_apr17/solve.gms:91`. ✓
- **30 iterations / 4 strategies → up to 7 cycles**: arithmetic correct. ✓
- **`lp_nlp_apr17` has same 4 input scalars with same defaults**: confirmed against `lp_nlp_apr17/input.gms:8-13`. ✓
- **`s80_resolve_option` declared only in `nlp_apr17`**: confirmed — not present anywhere in `lp_nlp_apr17/*.gms`. ✓
- **`s80_obj_linear` declared only in `lp_nlp_apr17`**: confirmed — not present anywhere in `nlp_apr17/*.gms`. `lp_nlp_apr17/declarations.gms:15`. ✓
- **NLP "relaxation" framing**: correctly notes that `nlp_apr17` has no LP-warmstart-style nonlinear-term fixing; its only "relaxation" is `s80_resolve_option = 3`'s switch to `conopt4.op2` with `Lim_Variable = 1.e25`. ✓
- **`lp_nlp_apr17` LP-relax path via `nl_relax.gms`**: confirmed — `$batinclude "./modules/include.gms" nl_relax` at `lp_nlp_apr17/solve.gms:113`. ✓

---

### Bugs Found

#### Q2-B1: `s80_resolve_option` cited at wrong line number

- **Severity**: Minor
- **Class**: 10 (Stale file:line citation)
- **Trigger**: Off-by-few line citation where adjacent lines say similar things (Minor tier)
- **Claim in answer**:
  - "additional scratch scalar in `nlp_apr17/declarations.gms:13-14`"
  - "`s80_resolve_option` | 0 (counter) | `nlp_apr17/declarations.gms:14`"
  - "`s80_resolve_option`** (`nlp_apr17/declarations.gms:14`)"
  - "`s80_resolve_option` | 0 | `nlp_apr17/declarations.gms:14`"
- **Reality in code**: `s80_resolve_option` is declared at `nlp_apr17/declarations.gms:15`. Line 14 contains `s80_counter`, not `s80_resolve_option`.
- **File evidence**: `modules/80_optimization/nlp_apr17/declarations.gms`:
  ```
   13  scalars
   14    s80_counter          counter (1)
   15    s80_resolve_option   option for resolve (1)
   16  ;
  ```
- **Tier reasoning**: Adjacent-line drift to a different scalar. A careful reader would notice the immediately-adjacent `s80_counter` and not be misled into a wrong action; the cited scalar at the wrong line is in the same 4-line scalars block. → **Minor** (per anchor: "Off-by-few line citation where adjacent lines say similar things").
- **Doc_error vs answerer_confabulation**: **doc_error** propagated. `magpie-agent/modules/module_80.md:316` already cites `s80_resolve_option` at `nlp_apr17/declarations.gms:14`. The answerer trusted the doc rather than re-reading source.
- **Anchor reference**: 2026-04-20 (R20) anchor "file:line citations drifted by 5-20 lines" — but this is an off-by-one, smaller magnitude. Closer to the "stale citation" pattern (Pattern 10).

#### Q2-B2: `s80_counter` implicitly cited at wrong line (via range "13-14")

- **Severity**: Minor
- **Class**: 10 (Stale file:line citation)
- **Trigger**: Same as Q2-B1 — off-by-few in adjacent content.
- **Claim in answer**: "additional scratch scalar in `nlp_apr17/declarations.gms:13-14`" — this range labels two lines, both of which actually live further down (lines 14-15).
- **Reality in code**: Line 13 = `scalars` (keyword), line 14 = `s80_counter`, line 15 = `s80_resolve_option`. The range `13-14` covers only `scalars` + `s80_counter`, not the s80_resolve_option the answer is naming.
- **File evidence**: Same as Q2-B1.
- **Tier reasoning**: Compound off-by-one — both the range and the in-table line citation are systematically shifted by 1. Same minor magnitude as Q2-B1; consolidated here for completeness but not double-counting severity.
- **Doc_error vs answerer_confabulation**: **doc_error** — `module_80.md:309` cites range `nlp_apr17/declarations.gms:8-13` and `module_80.md:315` cites `s80_counter` at line 13. The actual scalars block spans lines 13-16 (with 13 = `scalars` keyword, 14-15 = the two scalars, 16 = `;`).
- **Note**: This bug overlaps causally with Q2-B1 (same root cause, same source). The auditor counts it as a separate bug because two distinct citations are wrong, but the severity contribution is treated as a single Minor (combined cost to user is unchanged from a single wrong-line citation).

#### Q2-B3: Undercount of `s80_secondsolve` injection points in `lp_nlp_apr17`

- **Severity**: Minor
- **Class**: 6 (Hardcoded counts drift) — secondary to a misleading characterization
- **Trigger**: Wrong number; right concept (Minor — would not mislead into action)
- **Claim in answer**: "in `lp_nlp_apr17` the second solve fires after both the LP solve and the NLP solve (**two distinct injection points**), whereas in `nlp_apr17` it fires only after the single NLP solve"
- **Reality in code**: `lp_nlp_apr17/solve.gms` has at least **8 distinct `s80_secondsolve` injection points** at lines 66, 77, 131, 140, 150, 159, 190, 197 — covering LP solve, LP-landdiff solve, main NLP solve, three NLP retry/modelstat-13 paths, and two CPLEX add-solve paths. "Two distinct injection points" understates by 4×.
- **File evidence**: `grep -n "s80_secondsolve" modules/80_optimization/lp_nlp_apr17/solve.gms`:
  ```
   66:    if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
   77:      if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_landdiff; );
  131:  if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
  140:      if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
  150:      if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
  159:      if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
  190:if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_cost_glo; );
  197:  if(s80_secondsolve = 1, solve magpie USING nlp MINIMIZING vm_landdiff; );
  ```
- **Tier reasoning**: The concept (secondsolve fires more broadly in lp_nlp_apr17) is right; the count is wrong. The user would not act incorrectly on this; a comparative point in a contrast table is descriptive flavor, not safety-critical. → **Minor**. Borderline Major if the user were e.g. planning to instrument every secondsolve fire-point for telemetry, but no such hint in the question.
- **Doc_error vs answerer_confabulation**: **answerer_confabulation** — the docs (e.g., `module_80.md:814`) accurately list "solve.gms:66, 77, 131, 140, 190, etc." and `module_80.md:153` shows the secondsolve in the LP-landdiff branch as well. The answerer compressed this to "two distinct injection points" without re-grepping.

#### Q2-B4: Missing two `lp_nlp_apr17`-only scalars from the contrast (`s80_add_cplex`, `s80_add_conopt3`)

- **Severity**: Informational
- **Class**: 4 (Conceptual pseudo-code / incomplete enumeration) — borderline structural simplification
- **Trigger**: Descriptive incompleteness on a structural feature; would not mislead into action.
- **Claim in answer**: The contrast table presents `s80_obj_linear` as the single declaration-level difference on the `lp_nlp_apr17` side ("**Not declared** in `nlp_apr17`"). It also asserts "The four input scalars … carry the same defaults in both realizations … The declaration-level divergence is `s80_resolve_option` (only `nlp_apr17`) vs. `s80_obj_linear` (only `lp_nlp_apr17`)."
- **Reality in code**: `lp_nlp_apr17/solve.gms` also assigns and uses `s80_add_cplex` (line 31, 183) and `s80_add_conopt3` (line 34, 136) — these are scalars that don't exist in `nlp_apr17`. They appear to be set conditionally via `$ifthen` on `c80_nlp_solver` switch values rather than being declared with defaults in input.gms / declarations.gms, so they're not in the formal scalars list — but functionally they are additional realization-level state.
- **File evidence**: `lp_nlp_apr17/solve.gms:27-35`:
  ```
   27 $ifthen "%c80_nlp_solver%" == "conopt4"
   28   option nlp        = conopt4;
   29 $elseif "%c80_nlp_solver%" == "conopt4+cplex"
   30   option nlp        = conopt4;
   31   s80_add_cplex     = 1;
   32 $elseif "%c80_nlp_solver%" == "conopt4+conopt3"
   33   option nlp        = conopt4;
   34   s80_add_conopt3   = 1;
   35 $endif
  ```
- **Tier reasoning**: Since these aren't in the input.gms / declarations.gms scalars blocks the question explicitly asked about, omitting them is defensible. Question said "scalars … that control solver behavior" — these arguably qualify, but their assignment-without-declaration pattern means they're not in the canonical list. → **Informational** (style / scope choice).
- **Doc_error vs answerer_confabulation**: split-attribution — doc covers them (module_80.md mentions them indirectly via `c80_nlp_solver`), but the contrast table the answerer constructed was scoped to "declared scalars" only.

---

### Missing Nuances

- **Sign-of-life on the line citation drift**: the answer's footer says "verified 2026-05-16 against `nlp_apr17/*.gms` and `lp_nlp_apr17/*.gms`" — this is in tension with the Q2-B1/B2 citation errors. If the source files had truly been re-read at audit time, the off-by-one would have been caught. The 🟡 epistemic badge is technically defensible (docs cited, not source re-verified this session), but the footer overclaims session-level verification.
- **`s80_secondsolve` in `nlp_apr17` retry loop**: the answer says secondsolve "fires only after the single NLP solve" in `nlp_apr17`. Actually, `nlp_apr17/solve.gms:71` has secondsolve inside the retry loop too — so it fires after the initial solve (line 36) AND after every retry solve (line 71). Two injection points, not one. (This mirrors Q2-B3 in the opposite direction: undercount in nlp_apr17 too.) Tier: would-be-Informational; folding into B3's class rather than counting separately.
- **`s80_resolve_option = 3` does not "relax internal variable-bound checking"** strictly — `Lim_Variable = 1.e25` raises the maximum allowed variable value (helps with very-large numbers / scaling), it's not "internal bound checking" in the typical sense. Phrasing is loose but defensible as user-facing prose. Tier: would-be-Informational; not counted.

---

### Phase-2b Gate Assessment

The Q2 gate text: "answer must use the new `nlp_apr17` Parameters table. If the answer pulls scalars from `lp_nlp_apr17/declarations.gms` for default-behavior claims, the 2b sweep was superficial."

**Letter of the gate**: PASS. The answer rooted all default-behavior claims in `nlp_apr17` files. No scalar default was sourced from `lp_nlp_apr17`. The `lp_nlp_apr17` citations appear only in the explicit contrast section.

**Spirit of the gate**: PARTIAL PASS. The 2b sweep added the new `nlp_apr17` Parameters table at `module_80.md:309-316`. But that table's `declarations.gms:14`/`13` line citations are off-by-one from the actual file. The sweep populated the table without verifying its line numbers against source — so the answerer faithfully reproduced wrong line numbers from the new table. The 2b sweep was structural but not verifying.

**Recommendation**: Phase 2b should add a citation-verification pass to validator infrastructure (`scripts/check_gams_citations.sh` or a similar `check_default_realization_param_table.py`) that grep-confirms every `s\d+_*` declaration cited in module_*.md actually lives at that line number. The current `validate_consistency.sh` Check 17 may already cover this — if so, it didn't run on M80 in Phase 2b, or it gave a false-negative on these specific cells.

---

### Doc_error vs Answerer_confabulation Split

- **doc_error**: Q2-B1, Q2-B2 (both inherited from `module_80.md:309, 315-316`)
- **answerer_confabulation**: Q2-B3 ("two distinct injection points" was a compressed/inaccurate summary not present in the docs)
- **mixed**: Q2-B4 (Informational, scope choice — both layers complicit)

So: 2 doc-errors, 1 confabulation, 1 mixed. The dominant pattern is **doc citation drift** propagating verbatim.

---

### Severity Score

| Severity | Count |
|---|---|
| 🔴 Critical | 0 |
| 🟠 Major | 0 |
| 🟡 Minor | 3 (B1, B2, B3) |
| 🟢 Informational | 1 (B4) |

`raw_severity_weighted = 4·0 + 2·0 + 1·3 + 0·1 = 3`

`score_0_10 = max(0, 10 - 3) = 7`

**However**: per rubric §1 tie-breaker ("pick the lower"), and noting that Q2-B1 and Q2-B2 are causally **the same off-by-one error** manifested as two citations — consolidating them as a single Minor cuts the count to 2 Minor + 1 Informational:

`raw_severity_weighted = 4·0 + 2·0 + 1·2 + 0·1 = 2`

`score_0_10 = max(0, 10 - 2) = 8`

**Final score: 8/10** (Mostly Accurate)

The consolidation is defensible because the rubric anchors penalize one wrong citation per file:line drift event, not per occurrence of the same wrong citation throughout a single answer. If the rubric strictly counted occurrences, the score would be 7/10. Reporting 8/10 with the consolidation reasoning explicit; trend analysis can apply either convention consistently.

---

### Summary

Strong structural answer that nails the active realization, four input-scalar defaults, the 4-strategy retry cycle mechanism, and the realization-asymmetry between `nlp_apr17` and `lp_nlp_apr17`. Three Minor bugs: two are linked off-by-one citation drifts on `nlp_apr17/declarations.gms` line numbers (15 vs cited 14 for `s80_resolve_option`; 14 vs cited 13 for `s80_counter`), inherited from a pre-existing doc bug in `module_80.md:309-316`. One Minor undercount of `s80_secondsolve` injection points in `lp_nlp_apr17` (8 sites, not 2) is answerer-introduced. Phase 2b gate PASSED on the letter (no `lp_nlp_apr17` defaults pulled for default-behavior claims) but PARTIALLY FAILED on spirit (the new `nlp_apr17` Parameters table was populated without verifying line-number citations against source). Doc_error : answerer_confabulation = 2 : 1.

**Recommended remediation** (not in scope of this audit): correct `module_80.md:309, 315, 316` line numbers (8-13 → 8-16; 13 → 14; 14 → 15), and either fix `s80_secondsolve` contrast wording or add a structured table of all `s80_secondsolve` injection points by file:line.
