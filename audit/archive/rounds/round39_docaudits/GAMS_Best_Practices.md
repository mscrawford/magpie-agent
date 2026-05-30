# Round 39 Doc Audit: reference/GAMS_Best_Practices.md

**Auditor**: Opus 4.8 (1M)  | **Date**: 2026-05-30
**Ground truth**: official GAMS docs (gams.com/latest) for GAMS-language claims; `/tmp/magpie_develop_ro` for MAgPIE-convention claims.
**Doc role**: Phase 6 of the GAMS Programming Reference — generic best-practices / numerical-stability / debugging / performance guidance, sprinkled with MAgPIE-specific examples. The bulk is GAMS pedagogy ("Good vs Bad" snippets with placeholder variable names). Only a handful of claims are load-bearing about MAgPIE's actual interface.

---

## Method

1. Read the full doc (798 lines).
2. Extracted every code-checkable claim: MAgPIE interface names (`vm_*`/`pm_*`/`pcm_*`/`q*`), the `m_weightedmean` macro text, the `ct(t)` mechanism, the cost-unit string, the default NLP solver, and GAMS-language claims (`.scale`/`scaleopt`, `model.solvestat`, `limrow`/`limcol` defaults, `option tuning`).
3. Classified each identifier as **pedagogical placeholder** (generic "Bad/Good" example — not a claim about MAgPIE) vs **load-bearing** (used/claimed as a real MAgPIE artifact). Only load-bearing claims are bug-eligible per the doc's own framing.
4. Verified each load-bearing claim against code (two methods + positive control where an absence was at stake). Note: `rg` highlighting repeatedly **truncated the matched-name prefix** in output (showing `n(...)` for `pm_land_hist(...)`, `n(t_all,i)` for `im_pop(t_all,i)`); plain `grep -n` gave the untruncated line. All absence/presence calls below were re-confirmed with `grep` after that artifact was identified.

---

## Verified Claims (correct)

| Doc line | Claim | Evidence |
|---|---|---|
| 135 | `$macro m_weightedmean(x,w,s) (sum(s,x*w)/sum(s,w))$(sum(s,w)>0) + 0$(sum(s,w)<=0)` | `core/macros.gms:16` — identical (doc omits trailing `;`, immaterial for an illustrative snippet). ✓ |
| 331 | warm start `vm_land.l(j,land) = pcm_land(j,land); * Previous solution` | `pcm_land(j,land)` declared `core` of 10_land as "Land area in previous time step including possible changes after optimization" (`modules/10_land/landmatrix_dec18/declarations.gms:11`); set `pcm_land(j,land)=pm_land_start(j,land)` at `start.gms:11` and `=vm_land.l` in postsolve. Accurate. ✓ |
| 438,469 | `q10_land_area.l/.m` used in debugging examples | `q10_land_area(j2)` is a real equation: `modules/10_land/landmatrix_dec18/equations.gms:13`; declared `declarations.gms:27`. ✓ |
| 463 | `display pm_land_start;` | `pm_land_start(j,land)` real: `modules/10_land/landmatrix_dec18/declarations.gms:9`. ✓ |
| 589,598 | `pm_land_hist(t,j,land)` in fixed-variable pitfall example | `pm_land_hist(t_ini10,j,land)` real: `modules/10_land/landmatrix_dec18/declarations.gms:10`. (doc's `(t,...)` dims are looser than actual `(t_ini10,...)`, but this is an illustrative snippet, not a dimensionality claim.) ✓ |
| 597 | `if (t_past(t), ...)` | `t_past(t_all)` real set: `core/sets.gms:177`. ✓ |
| 50 | Cost unit "mio. USD17MER" | Confirmed in code: 8 hits in `modules/11_costs/*/declarations.gms`; e.g. `vm_cost_land_transition(j) ... (mio. USD17MER per yr)` (`10_land/.../declarations.gms:22`). ✓ |
| 706-708 | `ct(t) = yes` is set in core/calculations.gms before each solve; current-timestep marker with one element | `core/calculations.gms`: `ct(t)=no` (l.33), then inside the timestep loop `ct(t)=yes` (l.43) immediately before the `solve` batinclude (l.76); cleared again (l.95). `set ct(t) Current time period;` (`core/sets.gms:218`). Accurate. ✓ |
| 339-345 | "CONOPT - Good for sparse, large-scale NLP"; `option nlp = conopt; * Default` | MAgPIE default solver is conopt4: `config/default.cfg:2289` `cfg$gms$c80_nlp_solver <- "conopt4"  # def = conopt4`. CONOPT-is-default is accurate (the `option nlp=conopt` line is generic GAMS pedagogy, not a MAgPIE-syntax claim). ✓ |
| 82,89 | `.scale` attribute + `model.scaleopt = 1` | GAMS `scaleOpt` model attribute = "Employ user specified variable and equation scaling factors" (gams.com UG model-attributes). Valid. ✓ (🔵/🟡 — GAMS doc fetch confirmed scaleOpt; `.scale` is established GAMS.) |
| 419,494 | `model.solvestat <> 1` to detect failed solve | `solvestat = 1` = Normal Completion (established GAMS semantics, 🔵). Used correctly. Detailed-options fetch was truncated by the fetcher, but the convention is standard and correctly applied. ✓ |
| 427 | `option limrow = 3; * ... (default ...)` | `limrow`/`limcol` default = 3 (established GAMS, 🔵). gams.com option pages confirm the options exist and "0 suppresses the listing"; the detailed default table was truncated by the fetcher but 3 is the long-standing default. ✓ |

---

## Bugs Found

### Bug GBP-B1 — `option tuning = 1;` is not valid GAMS syntax
- **Severity**: **Minor**
- **Class**: 4 (Conceptual pseudo-code presented as real syntax) / GAMS-language factual error
- **Trigger (§1 Minor)**: "Wrong detail, but a careful reader wouldn't be misled into action or misunderstanding" — copy-pasting it yields an immediate GAMS compile error ("unknown option"), not a silent wrong result; low blast-radius, pedagogical MIP-tuning snippet.
- **Claim in doc** (lines 353-359):
  ```gams
  * Use Cplex tuning tool
  option mip = cplex;
  option tuning = 1;
  solve model using mip minimizing cost;
  ```
- **Reality**: GAMS has NO `tuning` option settable via the `option` statement. `tuning` is a **CPLEX solver option** set in `cplex.opt`, invoked via `<model>.optfile = 1;`. Verified against two GAMS pages: (a) the GAMS options list contains no `tuning` (only `profileTol` contains "tun"); (b) the CPLEX solver manual lists `tuning` as a CPLEX option ("invokes parameter tuning tool") read from `cplex.opt` after `ModelName.OptFile = 1;`.
- **File evidence**: gams.com/latest/docs/UG_GamsCall.html (no `tuning` GAMS option); gams.com/latest/docs/S_CPLEX.html (`tuning` is a CPLEX option file setting).
- **verify_cmd**: WebFetch UG_GamsCall.html "list every option whose name contains 'tun'" -> result: only `profileTol`; "no parameter or option named 'tuning' ... `option tuning = 1;` is not valid GAMS syntax". WebFetch S_CPLEX.html -> "CPLEX automatic tuning is invoked via a CPLEX solver option file (cplex.opt), not through a GAMS option statement. The exact name ... is `tuning`."
- **confirmed**: true.
- **Proposed fix**: replace the snippet body with the option-file mechanism:
  ```gams
  * Use the Cplex parameter tuning tool (a Cplex solver option, set in cplex.opt)
  option mip = cplex;
  model.optfile = 1;        * tells Cplex to read cplex.opt
  * cplex.opt contains:  tuning 1
  solve model using mip minimizing cost;
  ```

---

## Deferred (uncertain / not code-verifiable / pedagogical — NOT edited)

- **`pm_population` (line 486) and `pm_total_land` (line 490)** do NOT exist in develop (confirmed: `grep -rc pm_population modules/09_drivers/aug17/declarations.gms` -> the real population params are `im_pop(t_all,i)` / `im_pop_iso(t_all,iso)`; `grep -rln pm_total_land modules/` -> empty, exit 1). BUT both appear inside the generic "4.4 Validation Checks -> Add assertions to verify assumptions" block as illustrative `abort$(...)` patterns, NOT as claims that MAgPIE owns these parameters. Flagging them would be a false positive against pedagogical placeholders (same category as `vm_gdp`, `vm_big_number`, `vm_production`, etc. throughout the doc). **Borderline** — if the maintainers want these examples to use real MAgPIE names, `pm_population`->`im_pop` and `pm_total_land`->`sum(land, vm_land.l(j,land))`-style would be more faithful, but this is an editorial preference, not a code-verifiable doc bug. Left for human judgment.
- **`pm_land_hist(t,j,land)` dims** (lines 589,598) — real param is `(t_ini10,j,land)`. The doc's `(t,...)` is looser, but inside an illustrative pitfall snippet; not a dimensionality assertion. Not flagged.
- **`limrow`/`limcol` default = 3** and **`solvestat = 1` = Normal Completion** — the WebFetch of the GAMS detailed-options/model-status tables was truncated by the fetcher and did not return the explicit integers. Both values are long-standing, well-established GAMS semantics and the doc applies them correctly, so I treat them as verified-by-general-knowledge (🔵) rather than flagging; noting here only that I could not pull the literal table line from gams.com this session.
- **Unit-table magnitude ranges** (lines 49-55, e.g. "Land area ... 0.01 - 100", "Prices USD/ton 100 - 10,000") — illustrative order-of-magnitude guidance, not exact code claims; not code-verifiable as right/wrong.

---

## Pre-run advisory verdict

The pre-run checker said: "Verify GAMS-language claims vs gams.com; verify any MAgPIE-specific convention vs develop + GAMS_MAgPIE_Patterns.md. Flag real errors only."
- **Confirmed**: one real GAMS-language error (GBP-B1, `option tuning`). All MAgPIE-convention claims that are load-bearing (macro, `pcm_land`/`pm_land_start`/`pm_land_hist`/`q10_land_area`/`t_past`, USD17MER, CONOPT default, `ct` mechanism) verified correct against develop. No wrong realization, no inverted default, no invented load-bearing interface variable, no consumer/populator-set claim to mis-state (this doc makes none).

## Summary

26 code-checkable claims examined. 1 confirmed bug: `option tuning = 1;` (line 357) is invalid GAMS — CPLEX `tuning` is a cplex.opt solver option (Minor). All load-bearing MAgPIE claims verified correct. Two non-existent param names (`pm_population`, `pm_total_land`) are pedagogical placeholders, not interface claims -> deferred, not flagged.
