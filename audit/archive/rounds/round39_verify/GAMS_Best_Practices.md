# Round 39 Adversarial Verification — GAMS_Best_Practices.md

Target doc: `<magpie-agent>/reference/GAMS_Best_Practices.md`
Verifier: adversarial (Opus). Ground truth: official GAMS language docs (gams.com/latest).
Bugs verified: 1 (GBP-B1).

---

## GBP-B1 — `option tuning = 1;` is not a valid GAMS option statement

- severity: Minor
- bug_class: Conceptual pseudo-code / GAMS-language factual error
- class (this verifier): **other** (GAMS-language factual / prose-snippet error; not a MAgPIE consumer/producer/realization claim)
- verdict: **UPHELD**
- citation_ok: **true**

### STEP A — Mechanical citation check

Target doc:
```
$ test -f reference/GAMS_Best_Practices.md  -> EXISTS
$ wc -l reference/GAMS_Best_Practices.md    -> 797   (line 357 in range)
```

Read of lines 353-359 (Read tool, cat -n):
```
353 **Solver tuning** (for MIP):
354 ```gams
355 * Use Cplex tuning tool
356 option mip = cplex;
357 option tuning = 1;
358 solve model using mip minimizing cost;
359 ```
```
-> Line 357 contains the exact token `option tuning = 1;`. Lines 355/356/358 match the
auditor's quoted snippet verbatim. Citation reproduces.

The proposed_fix contains no `modules/.../file.gms:LINE` citations (it is a replacement code
snippet), so there are no further file:line citations to mechanically validate.

### Reality-claim verification (official GAMS docs)

The auditor's two reality claims were each checked against the authoritative gams.com pages.

1. "GAMS has no 'tuning' option settable via the option statement."
   - `UG_OptionStatement.html` (WebFetch): full enumeration of valid `option` keywords
     (output control, solver parameters, solver selection, program control, identifier
     options). **No keyword `tuning` appears.** The only `tun`-adjacent name is `profileTol`.
   - `UG_GamsCall.html` (WebFetch, the auditor's cited file_evidence): "The page does not
     contain the word 'tuning' or any option called 'tuning'."
   - => `option tuning = 1;` is NOT a recognized GAMS option statement. Copy-pasting it yields
     a GAMS compile error (unknown option). Claim **confirmed**.

2. "'tuning' is a CPLEX solver option set in cplex.opt and invoked via <model>.optfile = 1;."
   - `S_CPLEX.html` (WebFetch, the auditor's cited file_evidence): "tuning" is listed under
     "Preprocessing and General Options" as a **CPLEX solver-option-file keyword**, description
     "invokes parameter tuning tool". The cplex.opt file is "one option or comment per line ...
     interpreted as an option name and value separated by any amount of white space" and is read
     when `ModelName.OptFile = 1`. Sibling options `tuningdettilim`, `tuningdisplay`,
     `tuningmeasure`, `tuningrepeat`, `tuningtilim` confirm `tuning` lives in the CPLEX namespace,
     not the GAMS option-statement namespace.
   - `UG_SolverUsage.html` (WebFetch): "To tell a solver to use an option file, one can set the
     optfile model attribute ... If its value is 1, the suffix is opt" -> for CPLEX this reads
     `cplex.opt`. So `model.optfile = 1;` is the correct activation syntax. Claim **confirmed**.

### Proposed fix — GAMS-syntax soundness check

Proposed replacement body:
```gams
* Use the Cplex parameter tuning tool (a Cplex SOLVER option, set in cplex.opt)
option mip = cplex;
model.optfile = 1;        * tells Cplex to read cplex.opt
* cplex.opt contains:  tuning 1
solve model using mip minimizing cost;
```
- `option mip = cplex;` — `mip` is a confirmed valid option-statement keyword. OK.
- `model.optfile = 1;` — confirmed correct attribute + value to make CPLEX read `cplex.opt`. OK.
- comment `* cplex.opt contains:  tuning 1` — correct cplex.opt format (name + value separated by
  whitespace, NOT `tuning = 1`), per S_CPLEX.html. OK.
- `solve model using mip minimizing cost;` — valid. OK.

The fix is GAMS-correct and addresses the error. Safe to apply.

### Minor non-load-bearing nuance (no action required)

The auditor's file_evidence parenthetical "only 'profileTol' contains 'tun'" is imprecise:
`profileTol` does not actually contain the substring "tun". This is an immaterial aside; the
load-bearing claim (no GAMS `tuning` option-statement keyword exists) is independently confirmed
by both UG_OptionStatement.html and UG_GamsCall.html. Does not affect the verdict.

### Disposition

UPHELD. citation reproduces; both reality claims confirmed against authoritative GAMS docs; the
proposed fix is GAMS-syntactically valid. Pass to fixer with the proposed_fix as written.
