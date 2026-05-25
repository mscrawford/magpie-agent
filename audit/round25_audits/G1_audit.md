drift_observed: false

## Audit Report: R25-G1 (Module 14 default realization + equations.gms list)

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10

### Calibration anchor status
This is a regression question carried since R22. Prior scores: R22 = 10/10, R23 = 10/10. R25 answer maintains the clean baseline — agent surface remains healthy on this anchor; no degradation despite the recent AGENT.md trim (per round25_design.md success gate D).

### Verified Claims (correct)

| Claim in answer | Verification |
|---|---|
| Default realization is `managementcalib_aug19` | ✅ `config/default.cfg:354` reads `cfg$gms$yields <- "managementcalib_aug19"          # def = managementcalib_aug19` |
| It is also the only realization | ✅ `modules/14_yields/module.gms:31` has a single `$Ifi` branch for `managementcalib_aug19`. The sibling `modules/14_yields/input/` directory contains input data files (`.cs3`, `.mz`, `.csv`) — there is no `realization.gms` there, so it is not a realization. |
| Exactly 2 equations defined in `equations.gms` | ✅ `grep -n "^q14_" equations.gms` returns exactly 2 hits: line 14 (`q14_yield_crop`) and line 35 (`q14_yield_past`). |
| Equation names: `q14_yield_crop` and `q14_yield_past` | ✅ Verbatim match. |
| `q14_yield_crop` formula (verbatim quote) | ✅ Matches `equations.gms:14-16` exactly. |
| `q14_yield_past` formula (verbatim quote) | ✅ Matches `equations.gms:35-39` exactly. |
| `pm_past_mngmnt_factor` comes from Module 70 | ✅ Variable is consumed in q14 from M70's interface (consistent with module_14.md and the embedded comment block in equations.gms:24-28). |
| `s14_yld_past_switch` default = 0.25 at `input.gms:20` | ✅ `input.gms:20` reads `s14_yld_past_switch ... (1)     / 0.25 /`. |
| Did NOT include the historical-trap equation `q14_yieldcalib` | ✅ Correctly omitted — there is no such defined equation. |

### Mechanical checks
- **M1 (file:line citations present)**: PASS — `equations.gms:14-20`, `:24-39`, `:35-39`, `input.gms:20`, `module_14.md:3`.
- **M2 (active realization stated)**: PASS — explicit "is the default (and only) realization."
- **M3 (variable prefixes valid)**: PASS — `vm_yld`, `vm_tau`, `pm_past_mngmnt_factor`, `pcm_tau`, `i14_yields_calib`, `fm_tau1995`, `s14_yld_past_switch` all valid per Bug_Taxonomy.md Pattern 1.
- **M4 (epistemic badges present)**: PASS — uses 🟢, 🟡, 💬.
- **M5 (confidence-tier match)**: PASS (with a soft note — see Minor Nuances below).
- **M6 (closing source statement)**: PASS — explicit "Based on `modules/module_14.md`" + notes-file feedback.

### Bugs Found
None at Critical / Major / Minor severity.

### Minor Nuances (sub-Minor — not scored)
1. **Citation-range generosity** — The answer cites `q14_yield_crop` at `equations.gms:14-20` and `q14_yield_past` at `:24-39`. The actual GAMS equation bodies are tighter: lines 14-16 for crop and lines 35-39 for pasture; the trailing/leading `*'` comment blocks (lines 17-20, 24-34) are descriptive prose, not GAMS code. The answer self-corrects on the pasture equation by giving an explicit narrower citation ("`equations.gms:35-39` for the GAMS block"). A careful reader is not misled. Not a citation-drift bug (the cited code IS within the cited range), but a fully tight citation would be 14-16 and 35-39.
2. **🟢 tag on doc-sourced claims** — Sonnet stamps 🟢 on the equation quotes but its primary source statement is module_14.md (which is 🟡). Because Sonnet quotes verbatim against `equations.gms`, the 🟢 is defensible only if Sonnet actually read the file this session; the closing source statement leans on the doc, leaving this ambiguous. Stylistic only.

### Missing Nuances
None material. The answer correctly notes that `preloop`, `presolve`, `nl_fix`, and `nl_release` files contain extensive logic but are not GAMS equations (parameter assignments, conditionals) — this is the correct disambiguation and exactly the kind of preempt the rubric rewards on this anchor.

### Comparison to expected_answer_summary
The Sonnet answer matches the rubric expected_answer_summary on every material point:
- ✅ Default = `managementcalib_aug19`
- ✅ Exactly 2 equations
- ✅ Equation names `q14_yield_crop` + `q14_yield_past`
- ✅ Line ranges verified against `modules/14_yields/managementcalib_aug19/equations.gms`
- ✅ `q14_yieldcalib` (the historical trap) NOT included

No deviations. **drift_observed = false**.

### Summary
R25-G1 is a clean 10/10. Sonnet correctly identifies the default realization, correctly lists exactly the 2 defined equations with verbatim formulas, correctly maps cross-module dependencies (M70's `pm_past_mngmnt_factor`), and explicitly avoids the historical `q14_yieldcalib` trap. The agent surface for this calibration anchor is healthy and stable across R22 → R23 → R25, supporting success gate D (no degradation from the AGENT.md trim).
