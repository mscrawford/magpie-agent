# Round 29 — Design

**Date**: 2026-05-29 | **Type**: targeted — least-reliable NON-MODULE docs
**Schema**: validation_rounds.json v1.3 | rubric v1.2 | **Mode**: autonomous (user away; round + code-verified corrections; NO push)
**Verification source**: clean detached `origin/develop` worktree `/tmp/magpie-develop-r29` (ee98739fd)

## Why these docs (least-reliable rationale)

The flywheel has saturated module docs (R1-R6, R13-R28). The **non-module docs scored lowest on first validation and have gone ~3 months un-revalidated** while being edited:
- cross-module conservation (R7 = 6.9), architecture/safety/dependency (R8 = 6.0), helpers (R11 = 7.6; `debugging_infeasibility.md` was the **worst single doc at 5/10** — fabricated slack variable + wrong paths).
- R14-R28 were almost all module-mechanism probes, so these high-stakes, *actionable* docs (conservation laws, safety guidance, infeasibility debugging) are the most likely place residual unreliability hides.

Develop-drift is NOT the driver: only M21 + M32 code changed since the 2026-05-11 sync, both recently documented and dedup-locked. So R29 targets doc CLASSES not in the module dedup ledger (cross_module/, agent/helpers/) — fresh probe surface, different angle (conservation/safety/debugging) from the prior module-mechanism rounds.

## Regression rotation

R28 used G3+G4 (magpie4). R29 rotates back to **G1 + G2** (GAMS anchors; last run R27). Keeps all four exercised over R27-R29.

## Questions

| Q | Target doc | Archetype | Code-verifiable focus |
|---|-----------|-----------|----------------------|
| Q1 | land_balance_conservation.md | conservation law | q10 land-area equality, transition matrix, double-counting prevention |
| Q2 | water_balance_conservation.md | conservation law | supply/demand inequality + buffer; default sectors; unused water |
| Q3 | nitrogen_food_balance.md | conservation + supply=demand | food supply=demand mechanism + cropland N budget + surplus->emissions |
| Q4 | modification_safety_guide.md | safety / impact | high-centrality modules; what breaks if an interface var changes (real consumers) |
| Q5 | debugging_infeasibility.md | edge case / failure mode | common infeasibility causes; do the named constraints/switches/slack vars EXIST? |
| Q6 (G1) | regression anchor | M14 default realization | stability |
| Q7 (G2) | regression anchor | vm_carbon_stock M52/M56 propagation | stability |

Q5 deliberately re-tests the historically worst doc (R11 5/10): the auditor verifies every named cause/switch/slack-variable against develop code.

Full question text in `round29_answers/qN_answer.md` headers + `round29_synthesis.md`.
