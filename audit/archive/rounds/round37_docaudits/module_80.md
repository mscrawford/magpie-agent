# Round 37 Doc Audit — module_80.md (Optimization / Solver)

**Auditor**: Opus adversarial doc auditor (R37)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_80.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`

## Overall Verdict: ACCURATE
## Accuracy Score: 9/10

This is an unusually careful and accurate doc. All load-bearing claims (default realization, the 4-realization set, interface variables, parameter declarations + scalar defaults, the full solve sequences for all four realizations, the modelstat-7 silent-limbo analysis, fallback strategies, and the in-`.gms` file:line citations) are CORRECT and verifiable. The only defects are a small number of `config/default.cfg` line-citation drifts (the claims they support are all correct, the line numbers are off by 2-6 lines within the same config block) and one soft framing imprecision in a comparison-table cell. No Critical or Major bugs.

The pre-run advisory's concerns were checked specifically and all RESOLVE in the doc's favor except the config line-number drift (below):
- Default realization `nlp_apr17`: CONFIRMED (config/default.cfg:2282).
- Solver scalars (s80_*): CONFIRMED — defaults s80_maxiter=30, s80_optfile=1, s80_secondsolve=0, s80_toloptimal=1e-08 all match code + config.
- Optimization-loop control: CONFIRMED — retry loops, modelstat gates, s80_resolve_option cycling all match code.
- vm_cost_glo objective linkage: CONFIRMED — declared Module 11 (11_costs/default/declarations.gms:9), minimized in all realizations.
- c80_nlp_solver applies only to lp_nlp_apr17: CONFIRMED as a CLAIM (config comment line 2287 + lp_nlp solve.gms:27-35), but the doc CITES the wrong config line (see Bug 80-B1).

---

## Verified Claims (correct)

### Default realization & registration
- Default `nlp_apr17`: `config/default.cfg:2282` `cfg$gms$optimization <- "nlp_apr17"`. ✓ (doc line 4, 9, 10, 951-956)
- 4 realizations registered (lp_nlp_apr17, nlp_apr17, nlp_ipopt, nlp_par): `module.gms:24-27`. ✓ (doc cites module.gms:23-28 — the 23/28 are the R-SECTION marker lines; substance at 24-27. Acceptable.)
- `ls modules/80_optimization/`: exactly lp_nlp_apr17, nlp_apr17, nlp_ipopt, nlp_par. ✓ (MANDATE 8 satisfied)
- Equation count 0 (pure solver module): no equations.gms files in any realization. ✓

### Interface variables (MANDATE 13 — producer/consumer sets)
- `vm_cost_glo` provider = Module 11: declared `modules/11_costs/default/declarations.gms:9`. ✓ (doc line 40)
- `vm_landdiff` provider = Module 10: declared `modules/10_land/landmatrix_dec18/declarations.gms:15`; landmatrix_dec18 is the DEFAULT land realization (config:232). ✓ (doc line 47)
- nlp_apr17 actively uses ONLY vm_cost_glo (1 var); lp_nlp_apr17 uses both (2 vars). VERIFIED by grep: vm_landdiff appears in a MINIMIZING statement ONLY in lp_nlp_apr17/solve.gms (lines 76, 77, 196, 197). nlp_apr17/nlp_ipopt/nlp_par each carry `vm_landdiff,input,questionnaire` in their `not_used.txt` (declared-but-unused interface input). Doc's "1 vs 2 interface variables" framing is accurate at the level of active use. ✓ (doc lines 36-49)
- vm_cost_glo reference cite "nlp_apr17/solve.gms lines 34, 36, 70, 71": EXACT match to the four MINIMIZING vm_cost_glo statements. ✓ (doc line 40)

### nlp_apr17 (DEFAULT) — declarations / input / solve
- declarations.gms: p80_modelstat(t):9, p80_num_nonopt(t):10, s80_counter:14, s80_resolve_option:15. ✓ (doc lines 313-316)
- input.gms: s80_maxiter/30:9, s80_optfile/1:10, s80_secondsolve/0:11, s80_toloptimal/1e-08:12. ✓ (doc lines 322-325)
- solve.gms: option nlp=conopt4(14), threads=1(15), optfile=s80_optfile(16), scaleopt=1(17), solprint=0(18), holdfixed=1(19); primary solve(34); second solve(36); retry-loop entry `if (magpie.modelstat > 2`(47); repeat block(48-92); 4-strategy cycle via s80_resolve_option 1..4 (52-68); reset(89); until `modelstat<=2 or counter>=maxiter`(91); finalize p80_modelstat(95); GDX save gate `<=2`(98); abort gate `>2 and ne 7`(102). ALL ✓ (doc Steps 1-4, lines 227-292)

### Modelstat-7 silent-limbo analysis (doc Limitation 8, lines 828-841; table line 693)
- 7 > 2 → enters retry (solve.gms:47). ✓
- 7 fails `<=2` success-exit (solve.gms:91) → burns all s80_maxiter retries. ✓
- 7 fails GDX-save gate `<=2` (solve.gms:98) → no timestep GDX. ✓
- 7 excluded from abort gate `ne 7` (solve.gms:102) → no abort. ✓
- Doc's self-correcting note (line 839): the `modelstat=1 or 7` gate lives in lp_nlp_apr17/solve.gms:74 AND :194 and is the vm_landdiff-minimization gate, NOT a generic success check, and does NOT exist in nlp_apr17. VERIFIED EXACTLY (lp_nlp solve.gms:74 `if ((magpie.modelstat=1 or magpie.modelstat = 7)`, :194 same). ✓ Excellent, accurate self-correction.
- NA→13 retry cites nlp_apr17/solve.gms:44,87 and nlp_ipopt/solve.gms:70,91. ALL EXACT. ✓

### nlp_ipopt
- declarations.gms (15 lines): p80_modelstat(t):9, p80_num_nonopt(t):10, s80_counter:14; NO s80_resolve_option. ✓ (doc 435-439) — grep-confirmed s80_resolve_option absent (count 0), s80_counter present (positive control passed).
- input.gms (12 lines): s80_maxiter/30:9, s80_optfile/1:10, s80_toloptimal/1e-08:11; NO s80_secondsolve. ✓ (doc 445-449) — grep-confirmed s80_secondsolve absent in nlp_ipopt input.gms (count 0), present in the other three.
- preloop.gms (10 lines): `File optfile /ipopt.opt/`:9, `File optfile2 /ipopt.op2/`:10. ✓ (doc 460)
- solve.gms (111 lines): option nlp=ipopt(13); ipopt.opt written via put/putclose(18-29) with EXACTLY the 10 settings the doc lists (tol, mu_strategy monotone, mu_init 1e-5, mu_linear_decrease_factor 0.85, mu_superlinear_decrease_power 1.02, nlp_scaling_method none, bound_relax_factor 1e-7, honor_original_bounds yes, constr_viol_tol 1e-6, dependency_detector mumps); ipopt.op2 written(33-50) with the adaptive-mu settings the doc lists; magpie.optfile=s80_optfile(52); primary solve(62); retry loop(73-95) re-solving with SAME settings (no s80_resolve_option cycling); solprint=1 near cap(83-84); finalize(97-109) identical to nlp_apr17. ALL ✓ (doc 343-475, 648-652)
- "p80_modelstat(t) = 14 init" at solve.gms:10. ✓ (doc 698)
- Files table line counts (realization 20 / declarations 15 / input 12 / preloop 10 / solve 111): EXACT match to `wc -l`. ✓ (doc 457-461)

### lp_nlp_apr17
- declarations.gms: p80_modelstat(t):9, p80_num_nonopt(t):10, s80_counter:14, s80_obj_linear:15. ✓ (doc 200-203) — "4 declarations" claim (line 329) correct.
- input.gms: 4 scalars (s80_maxiter/30, s80_optfile/1, s80_secondsolve/0, s80_toloptimal/1e-08). ✓ (doc 209-212)
- solve.gms sequence: nl_fix(55); LP solve(65)+second(66); landdiff-min gate `modelstat=1 or 7`(74) → vm_cost_glo.up=vm_cost_glo.l(75), MINIMIZING vm_landdiff(76,77), vm_cost_glo.up=Inf(78); modelstat=2 abort "Unfixed nonlinear terms"(87-92); nl_release(104); nl_relax under `p80_modelstat(t)<>1`(112-113); full NLP solve(130); s80_add_conopt3 block(136-142); modelstat=13 retry optfile=2(145-152); modelstat=13 conopt3(155-161); s80_add_cplex polish block(183-202); GDX save `<3`(204); abort `>2 and ne 7`(208). ALL ✓ (doc Steps 1-10, lines 65-192)
- vm_landdiff cite "solve.gms lines 76, 77, 196, 197": EXACT. ✓ (doc 47)
- c80_nlp_solver switch consumed only by lp_nlp (uses %c80_nlp_solver% at solve.gms:27-35): CONFIRMED; nlp_apr17/nlp_ipopt/nlp_par do not reference it. ✓ (the CLAIM at doc 215, 327, 449, 957 is correct; only the config LINE cite drifts — Bug 80-B1)

### nlp_par
- declarations.gms: p80_modelstat(t,h):9, p80_counter(h):10, p80_handle(h):11, p80_extra_solve(h):12, p80_counter_modelstat(h):13, p80_resolve_option(h):14. ✓ (doc 504-511)
- solve.gms: solvelink=3(17); submission loop(37-46) with h2/i2/j2 activation + `solve ... MINIMIZING vm_cost_glo`(41) + p80_handle(h)=magpie.handle(45); collection repeat(49-135); handleStatus=2(51); execute_loadhandle(56); maxiter-fail debug block(70-78); handledelete(80); success/second-solve(82-94); resolve block 4-strategy cycle(96-127); final-check abort `>2 and ne 7`(137-140). ALL ✓ (doc Steps 1-6, lines 493-610)
- Critical requirement: Module 21 must use `exo` (fixed trade) — stated in realization.gms:11. ✓ (doc 483, 753)

### main.gms / global options
- `model magpie / all - m15_food_demand /;` main.gms:279. ✓ (doc 58)
- option iterlim=1000000, reslim=1000000, sysout=Off, limcol=0 (main.gms:281-284). ✓ (doc 707-711). [Code also has limrow=0 at 285, not listed by doc — not an error.]

### Downstream-effects example
- "Module 50 reads v50_nr_surplus_cropland.l in postsolve": v50_nr_surplus_cropland declared 50_nr_soil_budget/macceff_aug22/declarations.gms:16; `.l(i)` read in macceff_aug22/postsolve.gms:38. ✓ (doc 943) [The "(to calculate cumulative soil degradation)" gloss is a mild embellishment — postsolve.gms:38 just stores the level — but the core claim is correct.]

### CONOPT3 / CONOPT4 / solprint citations
- CONOPT4 cites (lp_nlp solve.gms:27-39, nlp_apr17:14-27, nlp_par:14-30): all land on the relevant solver-config blocks. ✓ (doc 637)
- CONOPT3 fallback cites (lp_nlp solve.gms:138-141, nlp_apr17:65-67): EXACT. ✓ (doc 643)
- solprint=0/=1 cite (solve.gms:16,174): matches lp_nlp_apr17 (solprint=0 at 16, =1 at 174). ✓ (doc 667)
- conopt4.opt preloop cite (nlp_apr17/nlp_par preloop.gms:8): EXACT (`File optfile /conopt4.opt/;` at line 8 in both). ✓ (doc 1000)

---

## Bugs Found

### Bug 80-B1 — Config citation drift for c80_nlp_solver claim
- **Severity**: Minor (tier_uncertainty: between Minor and Major; rubric tie-breaker pulls down. Trigger candidate: "citation drift to adjacent but different content". Lowered because the supported claim is correct and the correct content sits 2-6 lines below in the same config block, immediately visible.)
- **Class**: 10 (Stale/wrong file:line citation)
- **Doc lines**: module_80.md:449 and module_80.md:957
- **Claim in doc**: "...The `c80_nlp_solver` switch is **not** used by `nlp_ipopt` — that switch applies only to `lp_nlp_apr17` (config comment, `config/default.cfg:2285`)." (line 449); and "**cfg$gms$c80_nlp_solver** (solver selection — applies to `lp_nlp_apr17` only; see `config/default.cfg:2285`):" (line 957)
- **Reality in code**: `config/default.cfg:2285` is `cfg$gms$s80_maxiter <- 30`. The comment that the claim relies on ("Solver settings only for realization `lp_nlp_apr17`. All other realizations use `conopt4`.") is at **line 2287**, and the switch declaration `cfg$gms$c80_nlp_solver <- "conopt4"` is at **line 2291**. The CLAIM (c80_nlp_solver is lp_nlp_apr17-only) is correct.
- **File evidence**: `config/default.cfg:2285` (`cfg$gms$s80_maxiter <- 30`); `config/default.cfg:2287` (lp_nlp-only comment); `config/default.cfg:2291` (`cfg$gms$c80_nlp_solver <- "conopt4"`)
- **verify_cmd**: `grep -n "c80_nlp_solver" /tmp/magpie_develop_ro/config/default.cfg` → `2291:cfg$gms$c80_nlp_solver <- "conopt4"              # def = conopt4`; and Read of config:2282-2295 showing line 2285 = s80_maxiter, 2287 = the lp_nlp-only comment.
- **Anchor reference**: resembles R20 citation-drift anchor (line numbers off from final content) but milder (claim correct, drift small, same block).
- **confirmed**: true
- **proposed_fix**: replace both occurrences of `config/default.cfg:2285` with `config/default.cfg:2287` (the lp_nlp-only comment line). Exact replacements: line 449 `(config comment, config/default.cfg:2285)` → `(config comment, config/default.cfg:2287)`; line 957 `see config/default.cfg:2285` → `see config/default.cfg:2287`.

### Bug 80-B2 — Verification-footer config citation off by 2
- **Severity**: Minor (metadata footer; rubric: footer drift is Minor at most)
- **Class**: 10 (Stale file:line citation)
- **Doc line**: module_80.md:1038
- **Claim in doc**: "✅ Verified `nlp_apr17` remains the default in `config/default.cfg:2280`"
- **Reality in code**: the default declaration `cfg$gms$optimization <- "nlp_apr17"` is at **line 2282**, not 2280. Line 2280 is the last line of the nlp_par comment description.
- **File evidence**: `config/default.cfg:2282` (`cfg$gms$optimization <- "nlp_apr17"              # def = nlp_apr17`)
- **verify_cmd**: Read of `config/default.cfg:2266-2300` → line 2282 holds the default; 2280 is a comment line.
- **confirmed**: true
- **proposed_fix**: replace `config/default.cfg:2280` with `config/default.cfg:2282` on line 1038.

### Bug 80-B3 — Comparison-table cell implies lp_nlp_apr17 has s80_resolve_option
- **Severity**: Minor (tier_uncertainty: true; hedged by parenthetical and contradicted-correctly by the doc's own prose at line 329, which lists lp_nlp's 4 declarations WITHOUT s80_resolve_option)
- **Class**: 4 (conceptual imprecision) / borderline content-mismatch
- **Doc line**: module_80.md:471
- **Claim in doc**: comparison-table row `| s80_resolve_option | (LP-relax counter) | ✅ Declared (4-way cycle) | ❌ Not declared |` — the lp_nlp_apr17 cell reads "(LP-relax counter)".
- **Reality in code**: lp_nlp_apr17 does NOT declare or use `s80_resolve_option` at all (grep across all lp_nlp_apr17 files: 0 hits; positive control s80_counter present). Its relax/retry counter is `s80_counter` (solve.gms:9,119,120,173,177). The cell can be read as asserting lp_nlp_apr17 has an `s80_resolve_option` serving as an LP-relax counter, which is false.
- **File evidence**: `grep -rn s80_resolve_option modules/80_optimization/lp_nlp_apr17/` → no matches (exit 1); `lp_nlp_apr17/solve.gms:119` (`s80_counter = s80_counter + 1 ;`)
- **verify_cmd**: `rg -n "s80_resolve_option" /tmp/magpie_develop_ro/modules/80_optimization/lp_nlp_apr17/` → EXIT 1, no output; positive control `rg -n "s80_counter" .../lp_nlp_apr17/solve.gms` → lines 9,119,120,173,177.
- **confirmed**: true
- **proposed_fix**: change the lp_nlp_apr17 cell on line 471 from `(LP-relax counter)` to `❌ Not declared (relax counted by s80_counter)` to remove the implication that the scalar exists in lp_nlp_apr17.

---

## Deferred (not bugs; not editable — uncertain or non-doc-checkable)

- `config/default.cfg:2266-2278` cite (doc line 978) for the realization-comment block: actual block is 2267-2280. The substantive claim (block lists only nlp_apr17/lp_nlp_apr17/nlp_par; nlp_ipopt absent from the comment) is CORRECT and verified (config:2268,2270,2273; no nlp_ipopt). Range is off by ~1-2 lines at each end — within normal block-citation tolerance; not flagging to avoid over-flagging a correct, useful note. Could optionally tighten to 2267-2280.
- `s80_add_cplex` / `s80_add_conopt3` are USED in lp_nlp_apr17/solve.gms (31,34,136,145,183) but DECLARED NOWHERE in the repo (confirmed by repo-wide grep). This is a quirk of the actual MAgPIE code (GAMS implicit/late declaration or an upstream omission), NOT a doc defect — the doc does not claim these are declared. Out of audit scope.
- Doc line 187 lp_nlp finalization parenthetical "Success (modelstat < 3, excluding modelstat = 7)": code gate is `p80_modelstat(t) < 3` (solve.gms:204), which excludes 7 automatically since 7 is not < 3. The "excluding modelstat = 7" rider is redundant but not wrong. Not a bug.
- Doc line 711 comment "limcol = 0 // No column listing limit (full model)": `limcol=0` actually SUPPRESSES the column listing (limit of 0 columns); the gloss is arguably backwards, but it is an inline comment on a global GAMS option and the value itself (0) is correctly stated. Borderline; not flagging.
- Runtime-comparison numbers (lines 873-896) are explicitly labeled "made-up numbers for illustration" — not code-checkable; correctly disclaimed.

---

## Summary

module_80.md is ACCURATE (9/10). All Critical-prone surfaces — default realization, interface variable producers, scalar defaults, modelstat gates, the modelstat-7 silent-limbo behavior, and the 4-realization solve sequences — are correct and well-cited against develop. The pre-run advisory's flags were all checked: defaults and objective linkage CONFIRMED; the c80_nlp_solver lp_nlp-only claim is CONFIRMED as a claim but its config line cite drifts (Bug 80-B1). Three Minor citation/framing defects only (80-B1 config line 2285→2287; 80-B2 footer 2280→2282; 80-B3 comparison-table cell implying lp_nlp has s80_resolve_option). No Critical/Major bugs; no phantom or omitted consumers; no inverted defaults.
