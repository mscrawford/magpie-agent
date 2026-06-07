# Round 49 Verify — cbc-soil (carbon_balance_conservation.md)

Verifier: adversarial (Opus 4.8 1M). Ground truth: /tmp/magpie_develop_ro.
Target doc: cross_module/carbon_balance_conservation.md

---

## Bug cbc-soil-B1 — VERDICT: UPHELD

**Class**: other (file:line citation-precision claim; not a consumer/producer set, not a
realization equation-count). Adjudicated as a citation accuracy issue.

**Severity (auditor)**: Minor — concur.

### STEP A — Mechanical citation check

Cited file (file_evidence + both proposed_fix endpoints):
`modules/52_carbon/normal_dec17/input.gms`

```
$ test -f /tmp/magpie_develop_ro/modules/52_carbon/normal_dec17/input.gms
EXISTS
$ wc -l ...
96 lines
```
=> file exists; lines 8, 9-11, 22, 23 are all in range (<=96). citation_ok = TRUE.

Exact line reads (verbatim from /tmp/magpie_develop_ro/.../input.gms):
```
 8  $setglobal c52_carbon_scenario  cc
 9  *   options:  cc        (climate change)
10  *             nocc      (no climate change)
11  *             nocc_hist (no climate change after year defined by sm_fix_cc)
12  (blank)
...
16  table fm_carbon_density(...) LPJmL carbon density ...
22  $if "%c52_carbon_scenario%" == "nocc"      fm_carbon_density(...) = fm_carbon_density("y1995",...);
23  $if "%c52_carbon_scenario%" == "nocc_hist" fm_carbon_density(...)$(m_year(t_all) > sm_fix_cc) = ...;
```

`grep -n "c52_carbon_scenario" input.gms`:
```
8:$setglobal c52_carbon_scenario  cc
22:$if "%c52_carbon_scenario%" == "nocc" ...
23:$if "%c52_carbon_scenario%" == "nocc_hist" ...
```
Exactly three references: definition (8), nocc application (22), nocc_hist application (23).
No reference at line 12-21 or 24+.

### STEP C — Adjudication of the claim

Auditor's reality_in_code reproduces EXACTLY:
- The switch IS defined at line 8 (`$setglobal c52_carbon_scenario  cc`), default value `cc`.
- The three options are comments at lines 9-11.
- Lines 22-23 contain ONLY the `$if` APPLICATION logic for `nocc` (22) and `nocc_hist` (23).
- The default `cc` is the no-`$if` fallthrough; it does NOT appear at 22-23.
- Confirmed default elsewhere: `config/default.cfg:1569` -> `cfg$gms$c52_carbon_scenario  <- "cc"   # def = "cc"`.

Therefore the doc's citation `input.gms:22-23` is imprecise: a reader checking 22-23
finds `nocc`/`nocc_hist` but neither the switch definition nor the default `cc` — yet the
doc text at both locations leads with `cc` (the default) and lists all three scenarios.
The cited range under-covers what the prose describes.

Both doc occurrences confirmed present:
```
512:**Climate Scenarios** (Module 52, `modules/52_carbon/normal_dec17/input.gms:22-23`):
697:**Configuration** (Module 52, `modules/52_carbon/normal_dec17/input.gms:22-23`):
```

### Proposed fix assessment

Auditor proposes `input.gms:8-23` at both doc lines (512, 697).
- Line 8 = `$setglobal` switch definition + default `cc`. ✓
- Lines 9-11 = option comments (`cc`, `nocc`, `nocc_hist`). ✓
- Lines 22-23 = `nocc`/`nocc_hist` application logic. ✓
The 8-23 span covers definition + all three options + the application, matching the prose at
both 512-515 and 697-699. Fix is correct and safe (citation widening only; no semantic change).

### corrected_set
Change both doc citations (lines 512 and 697) from
`modules/52_carbon/normal_dec17/input.gms:22-23`
to
`modules/52_carbon/normal_dec17/input.gms:8-23`.

---

VERDICT: UPHELD. citation_ok=TRUE. Apply proposed fix (8-23) at doc lines 512 and 697.
