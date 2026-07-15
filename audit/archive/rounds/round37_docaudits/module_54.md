# Audit Report: module_54.md (Phosphorus — off)

**Doc**: `<magpie-agent>/modules/module_54.md`
**Ground truth**: `/tmp/magpie_develop_ro/modules/54_phosphorus/` (develop worktree)
**Audit date**: 2026-05-30
**Auditor**: Opus 4.8 (round37 doc audit)

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

Module 54 is a genuinely trivial module (off realization, 0 equations, 1 variable), and the doc's
core factual spine is correct and exceptionally well-cited. Every file:line citation into
`module.gms`, `realization.gms`, `declarations.gms`, `preloop.gms`, and `postsolve.gms` verified
exactly. The one substantive error is an architectural mis-routing of `vm_p_fert_costs` through
Module 38 in the "Related Modules" section, contradicted both by the actual code AND by the doc's
own Phase-1 integration text.

---

## Pre-run advisory verdict

The advisory flagged: "Verify default realization. Verify the phosphorus-budget equations and
consumer/producer sets; keep distinct from M50 (N budget). Both grep forms + positive control."

- **Default realization** → CONFIRMED CORRECT. `off` is the only realization (`ls` shows just
  `off/`) and the config default. `grep -n "phosphorus" config/default.cfg` → line 1587
  `cfg$gms$phosphorus <- "off"  # def = off`. Positive control: adjacent `cfg$gms$methane`
  (line 1583) and `cfg$gms$awms` entries present, proving the search works in that file region.
- **Phosphorus-budget equations** → CONFIRMED CORRECT. The off realization has NO `equations.gms`
  (`ls off/` → declarations.gms, postsolve.gms, preloop.gms, realization.gms only). Doc's
  "Equations: 0" is right.
- **Consumer/producer sets** → REFUTED THE DOC (1 bug, see B1). `vm_p_fert_costs` is consumed by
  exactly ONE module — Module 11 (costs) at `11_costs/default/equations.gms:25` — directly, not via
  Module 38. The doc's "Related Modules" section routes it 54→38→11.
- **Keep distinct from M50** → The doc DOES keep P distinct from N. Ironically, the correct
  architecture parallels M50: `vm_nr_inorg_fert_costs` (declared in M50, verified
  `50_nr_soil_budget/macceff_aug22/declarations.gms`) also feeds DIRECTLY into M11 q11_cost_reg
  (line 24), immediately above `vm_p_fert_costs` (line 25). The doc's M38-intermediary claim
  obscures this exact parallel.

---

## Verified Claims (correct)

| Doc claim | Doc line | Code evidence | Verdict |
|---|---|---|---|
| Default/only realization is `off` | 5 | config:1587; only `off/` dir | ✅ |
| Purpose "estimate major P-flows / P-pools" | 7 | module.gms:10-11 | ✅ |
| Module not activated; calcs disabled | 9 | module.gms:26-28, realization.gms:8-9 | ✅ |
| module.gms span 1-34 | 16 | wc -l = 34 | ✅ |
| realization.gms span 1-17 | 17 | wc -l = 17 | ✅ |
| declarations.gms span 1-17 | 18 | wc -l = 17 | ✅ |
| preloop.gms span 1-12 | 19 | wc -l = 12 | ✅ |
| postsolve.gms span 1-15 | 20 | wc -l = 15 | ✅ |
| Equations: 0 | 22 | no equations.gms in off/ | ✅ |
| Variables: 1 (`vm_p_fert_costs` fixed to zero) | 24 | declarations.gms:10 (1 variable) | ✅ |
| Author Benjamin Leon Bodirsky (module.gms:30) | 26 | module.gms:30 `@authors Benjamin Leon Bodirsky` | ✅ |
| `vm_p_fert_costs(i)` declared at declarations.gms:10 | 34 | declarations.gms:10 | ✅ |
| Fixed to zero at preloop.gms:10 | 37,43 | preloop.gms:10 `vm_p_fert_costs.fx(i)=0;` | ✅ |
| Deactivation purpose at realization.gms:8-9 | 48 | realization.gms:8-9 | ✅ |
| "still under development" realization.gms:11 | 125 | realization.gms:11 `@limitations The realization is still under development.` | ✅ |
| Future-enrichment quote module.gms:27-28 | 130 | module.gms:27-28 | ✅ |
| All 11 P-flow citations module.gms:14-24 | 65-117 | module.gms lines 14-24, one flow per line, all map exactly | ✅ |
| Only `off` realization exists (module.gms:33) | 426 | module.gms:33 is the `$Ifi "off"` include | ✅ |
| postsolve reports vm_p_fert_costs levels (all zeros) | 53-55 | postsolve.gms:10-13 write ov_p_fert_costs from .m/.l/.up/.lo | ✅ |

All 11 individual P-flow line citations (module.gms:14 through module.gms:24) were checked one by one
and each maps to the correct bullet. This is unusually clean citation work.

---

## Bugs Found

### Bug module_54-B1

- **Severity**: Major
- **Class**: 12 (content-level citation/attribution mismatch) + MANDATE 9 (cost-variable
  attribution) + MANDATE 17 (direct vs transitive consumer)
- **Trigger** (§1 Major): "Right concept, wrong number/attribution that misleads about behavior but
  won't directly cause damaging action." (Tempered from Critical because the section is framed
  hypothetically with "would", the variable name is correct, AND the doc names M11 correctly
  elsewhere — see Phase-1 text doc:304-306.)
- **Claim in answer** (doc:259-266):
  > "**4. Module 38 (Factor Costs)**: Would receive P fertilizer costs from Module 54. P fertilizer
  > costs added to total production costs in objective function.
  > **5. Module 11 (Costs)**: Would aggregate P fertilizer costs from Module 38. Total costs: Labor +
  > Capital + Land conversion + **P fertilizer** + N fertilizer + Irrigation + ..."
- **Reality in code**: `vm_p_fert_costs` is consumed by exactly ONE module — Module 11 (costs) —
  and it enters M11's regional cost equation DIRECTLY. It does NOT pass through Module 38. Module 38
  contains zero references to `vm_p_fert_costs`. The doc asserts a 54→38→11 routing; the actual
  routing is 54→11 direct. The correct parallel is the N inorganic fertilizer cost
  `vm_nr_inorg_fert_costs` (declared in Module 50, not 38), which sits on the line immediately above
  `vm_p_fert_costs` in the same q11_cost_reg equation.
- **File evidence**:
  - `/tmp/magpie_develop_ro/modules/11_costs/default/equations.gms:25` →
    `                   + vm_p_fert_costs(i2)` (inside `q11_cost_reg(i2) .. v11_cost_reg(i2) =e= ...`)
  - `/tmp/magpie_develop_ro/modules/11_costs/default/equations.gms:24` →
    `                   + vm_nr_inorg_fert_costs(i2)` (N analog, from M50)
  - Module 38 has NO reference (rg empty, EXIT=1).
- **verify_cmd + result**:
  - `rg -n "vm_p_fert_costs" /tmp/magpie_develop_ro/modules/ /tmp/magpie_develop_ro/core/` →
    declarations.gms:10, preloop.gms:10, postsolve.gms:10-13 (all in 54_phosphorus/off), and
    `modules/11_costs/default/equations.gms:25`. NO other module.
  - `grep -rn "vm_p_fert_costs" ...` (second method) → identical result set.
  - `rg -n "vm_p_fert_costs" /tmp/magpie_develop_ro/modules/38_factor_costs/` → empty, EXIT=1.
  - Positive control: M11 grep returns a hit, proving the search works.
- **Anchor reference**: Resembles R20 (wrong consumer set) but downgraded to Major per the
  tie-breaker because (a) the framing is explicitly hypothetical ("would"), (b) the variable name is
  correct, and (c) the doc independently states the correct M11 integration point at doc:304-306
  ("Integration with Module 11 (Costs): Add `vm_p_fert_costs` to objective function"), which is
  exactly right and contradicts the M38 claim. A reader would be misled about WHERE the cost
  integrates (M38 vs M11), but the variable itself is correctly identified.
- **Proposed fix**: Replace the doc:259-266 block with:
  > **1. Module 11 (Costs)**:
  > - `vm_p_fert_costs` is **already wired directly into** Module 11's regional cost equation
  >   `q11_cost_reg` (`modules/11_costs/default/equations.gms:25`), on the line immediately below the
  >   N inorganic fertilizer cost `vm_nr_inorg_fert_costs` (line 24, sourced from Module 50). It is
  >   currently fixed to zero (preloop.gms:10), so it contributes nothing, but the interface is
  >   present. An active realization would only need to populate `vm_p_fert_costs` with a real cost
  >   equation; no change to Module 11 or Module 38 is required.
  > - Note: P fertilizer cost does NOT route through Module 38 (Factor Costs). Module 38 has no
  >   reference to `vm_p_fert_costs`. This mirrors the N inorganic fertilizer cost, which comes from
  >   Module 50 (nr_soil_budget), not Module 38.

  And delete the Module 38 item (or demote it to: "Module 38 is NOT involved in P fertilizer cost
  routing — despite handling crop factor costs, fertilizer nutrient costs bypass it.").

---

## Non-bugs / judgement calls (NOT edited)

- **doc:35** — variable description rendered as "Costs for mineral **phosphorus** fertilizers";
  code (declarations.gms:10) says "costs for mineral fertilizers" (no word "phosphorus"). The doc is
  paraphrasing within an unambiguous P-module context, not presenting a verbatim quote, and adds
  "phosphorus" only as a contextual clarifier. Informational at most; left as-is.
- **doc:267** — groups "Module 51 (Nitrogen) and Module 53 (Methane)" under N-P-K interaction prose.
  This is forward-looking domain prose about nutrient interactions, not a code-checkable claim about
  current wiring. Not a bug.
- The entire "Intended Functionality", "Why Off", "Implications", "Future Development", and "Key
  Insights" sections are explicitly hypothetical/domain prose about a disabled module. They are NOT
  code-checkable behavior claims and were not audited as such (correctly framed with "would" /
  "intended" / "if active" throughout).
- **Declared output parameter `ov_p_fert_costs(t,i,type)`** (declarations.gms:15) is not mentioned
  in the doc's "Variables: 1" count. This is the standard `ov_*` reporting parameter and is
  conventionally not counted as a model variable; "Variables: 1" remains accurate. Not a bug.

---

## Deferred (could not fully verify / not code-checkable)

- Quantitative economic claims ("P fertilizer costs 10-20% of total fertilizer costs", "production
  costs underestimated by 5-10%", "P fertilizer ~20% of N costs per kg nutrient", "50-400 years
  phosphate reserves") — these are real-world/literature figures, not MAgPIE code facts, and the doc
  does not attribute them to code. Out of scope for a code audit; not flagged as bugs.

---

## Summary

One Major bug: the "Related Modules" section routes `vm_p_fert_costs` through Module 38
(54→38→11) when the code wires it directly into Module 11's `q11_cost_reg`
(`11_costs/default/equations.gms:25`); Module 38 has zero references to it. Everything else
verified clean — all ~25 file:line citations into the off realization are exact, default
realization (`off`) confirmed, 0 equations confirmed, and the single variable correctly identified.
The doc even contradicts its own M38 claim at doc:304-306 (correctly naming M11). Score 8/10.
