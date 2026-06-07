# Audit Report: Round 49 — Core_Architecture.md structural inventory (corearch)

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

Ground truth: `/tmp/magpie_develop_ro` (develop worktree). Realization counts cross-verified TWO ways that agree perfectly for all 46 modules: (a) `$include .../realization.gms` lines in each `module.gms` (authoritative MODULETYPES section), (b) subdirectory count excluding the `input` data directory. Positive control passed (52_carbon `=e=` found; module-80 grep correctly empty).

---

## Verified Claims (correct)

- **Module count = 46** — `ls -d /tmp/magpie_develop_ro/modules/*/` minus `include.gms` = 46. Core_Architecture.md:9 ("46 independent modules") correct.
- **Section 4.2 inventory (all 46 names)** — `diff` of the 46 names parsed from Core_Architecture.md §4.2 against the tree is IDENTICAL (no missing/extra). Answer's cross-check claim is correct.
- **Module 80: 4 realizations, default `nlp_apr17`** — `modules/80_optimization/module.gms` wires exactly `lp_nlp_apr17`, `nlp_apr17`, `nlp_ipopt`, `nlp_par`; `config/default.cfg:2282` = `cfg$gms$optimization <- "nlp_apr17"`. Answer cited line 2282 exactly. CORRECT.
- **Module 80 defines no equations** — no `equations.gms` in any realization; `grep`/`rg` for `=e=|=l=|=g=` over `modules/80_optimization/` returns nothing (positive control confirmed search works). `modules/80_optimization/nlp_apr17/solve.gms:34` = `solve magpie USING nlp MINIMIZING vm_cost_glo;` (exact). CORRECT.
- **Model declaration** — `main.gms:279` = `model magpie / all - m15_food_demand /;` verbatim. CORRECT.
- **Optimization / time-loop structure** — `core/calculations.gms` matches the doc and the answer's reproduction exactly. ALL 13 line citations verified exact: start (13), preloop (15), loop (40), presolve_ini (52), presolve (54), sm_intersolve=0 (57), while (59), solve (76), sm_intersolve=1 (79), intersolve (81), postsolve (87), Execute_Unload (92), put_utility save (99). The `while(sm_intersolve=0,...)` + Module-15-reset description is accurate.
- **12 phases** — the 12 batinclude phase names extracted from `main.gms` + `core/calculations.gms` are exactly: sets, declarations, input, equations, scaling, start, preloop, presolve_ini, presolve, solve, intersolve, postsolve. Matches Core_Architecture.md §5.1 and the answer. CORRECT.

---

## Bugs Found

### Bug corearch-B1 — realization count "40 of 46" is wrong; true value is 22 of 46
- **Severity**: Major
- **Class**: 6 (Hardcoded counts drift) / 15-adjacent (doc-propagated)
- **Trigger**: §1 Major — "Fabricated count for a set/parameter/realization list" (here an aggregate count + ~31 wrong per-module sub-counts), presented as verified-exact.
- **Claim in answer**: "Modules with Multiple Realizations: 40 — CORRECT ... Total: 25 + 10 + 5 = 40 of 46. The '~40' approximation is exact against the current tree." Plus per-module table (e.g. 14, 32, 52, 56 listed as 2 realizations; 41, 42, 53, 58 as 3; 18, 21, 38, 59 as 4).
- **Reality in code**: **22 of 46** modules have multiple realizations. Verified two independent ways that agree for ALL 46 modules: `module.gms` `$include realization.gms` count == subdir-count-excluding-`input`. The answer counted the **`input/` data directory** (present in 22 modules; holds only a `files` manifest, e.g. `14_yields/input/files`) as if it were a realization, inflating every such module by +1. `input` is NEVER wired as a realization (`grep '== "input"' */module.gms` → empty). Concretely: 18 modules the answer called "2 realizations" actually have **1** (09,10,12,14,15,20,22,28,32,35,39,43,50,52,56,57,62,73); 9 called "3" actually have **2** (13,29,40,41,42,44,53,58,60); of the 5 called "4", three (18,21,38) have **3** and one (59_som) has **2** (only 80 truly has 4). True multi-realization set (22): 13,18,21,29,30,31,34,37,38,40,41,42,44,51,53,55,58,59,60,70,71,80.
- **File evidence**:
  - `/tmp/magpie_develop_ro/modules/14_yields/module.gms` — single `$Ifi "%yields%" == "managementcalib_aug19" $include .../realization.gms` (1 realization, not 2).
  - `/tmp/magpie_develop_ro/modules/59_som/module.gms` — only `cellpool_jan23` + `static_jan19` (2, not 4).
  - `/tmp/magpie_develop_ro/modules/14_yields/input/files` — data manifest (`lpj_yields.cs3`, ...), confirming `input/` is data, not code.
  - `Core_Architecture.md:59` itself lists `input` as an execution PHASE, which is why every module has an `input/` directory.
- **Root cause**: `doc_error`. The "~40 of 46" originates in `AGENT.md:205` and its snippet `AGENT.md:207` (`ls -d ${m}*/`), which counts `input/` as a realization. The answerer trusted the doc AND reproduced the same `input`-counting bug in its own per-module table, then asserted it "exact" with a 🟢 verified tag. The answerer did NOT beat the doc; it amplified the error with false confidence. (Note: answer correctly attributed the figure to AGENT.md and correctly stated Core_Architecture.md states no realization count — but the figure it carried over is wrong.)
- **Anchor reference**: R6 "claimed 22 equations; actual 17 → Major" (fabricated count of a load-bearing structure). Magnitude here is larger (off by ~82%, and it is the literal subject of the probe), placing it at the severe end of Major; not Critical because no wrong default-realization / wrong-file / invented-name is produced (all defaults are correct), so it misleads about structure rather than causing a damaging edit (tie-breaker → lower tier).

---

## Latent doc bugs (recorded regardless of answer score)

### LATENT-1 — AGENT.md Step 1c "~40 of 46" + dir-count snippet are wrong (should be 22 of 46)
- **Doc location**: `AGENT.md:205` ("# Run this to see which modules have >1 realization (currently ~40 of 46):") and `AGENT.md:207` (`count=$(ls -d ${m}*/ 2>/dev/null | wc -l)`). Also deployed copies `../AGENT.md` / `../CLAUDE.md` (Check-10 sync).
- **Code reality**: 22 of 46 modules have multiple realizations. The glob `${m}*/` matches the `input/` data directory, so the snippet over-counts by exactly the number of modules that have an `input/` dir (22 of them). To be correct the snippet must exclude `input` (e.g. count `$Ifi ... realization.gms` lines in `module.gms`, or `find -type d -not -name input`).
- **Severity (future-reader harm)**: Major — a maintainer running the documented snippet to decide "does this module need Step 1c?" gets a wrong list (false positives like 14_yields, 52_carbon, 56_ghg_policy flagged as multi-realization). Load-bearing because Step 1c is an instructed, agent-run procedure.
- **Root cause**: `doc_error` (the doc/snippet is itself wrong; this round's answer reproduced it → counted in B1, not double-counted in score).
- **Fix**: update AGENT.md:205 to "currently 22 of 46" and AGENT.md:207 snippet to exclude `input` (then redeploy to ../AGENT.md + ../CLAUDE.md).

---

## Missing Nuances
- The answer's footer tags the realization counts 🟢 "read from ../modules/ directory tree" — but the directory-tree method (raw dir count) is exactly what introduced the error. A correct verification reads `module.gms` or excludes `input/`. This is the methodological reason the otherwise-careful answer went wrong; not a separate bug.
- `calculations.gms:72-74` mentions additional conditional sub-phases (`nl_fix`, `nl_release`, `nl_relax`) within solve; these are not part of the canonical 12 and the doc/answer are correctly silent on them.

## Summary
Seven of the answer's eight sections are fully correct with exact citations (module count 46, §4.2 inventory, module-80 4-realizations/default/0-equations, model declaration main.gms:279, the entire `calculations.gms` time-loop with all 13 line numbers verified, and the 12 phases). The sole error is the central realization-count claim: "40 of 46" should be **22 of 46**, caused by counting each module's `input/` data directory as a realization — a bug inherited from AGENT.md:205/207 and reproduced (and asserted "exact") by the answerer. One Major bug → score 8/10. One latent doc bug recorded against AGENT.md:205/207 to be fixed regardless.
