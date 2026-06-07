# Round 50 Verification — module_55.md (AWMS)

Verifier: adversarial (Opus 4.8 1M). Ground truth: `/tmp/magpie_develop_ro` develop worktree.

## Bug m55-awms-B1 — Wrong parameter default value (class 13)

**Doc claim (module_55.md:292):** "**Historical period** (≤ `sm_fix_SSP2`, typically 2015): Fixed at SSP2 baseline (`presolve.gms:20`)"

**Auditor reality:** `sm_fix_SSP2` default is 2025, not 2015 (off by 10 yr). File_evidence `default.cfg:225`. Proposed fix: on line 292 replace "typically 2015" with "2025 by default"; line 381 has no explicit year, needs no change.

### STEP A — Mechanical citation check

file_evidence = `/tmp/magpie_develop_ro/config/default.cfg:225`

```
$ test -f /tmp/magpie_develop_ro/config/default.cfg  -> EXISTS
$ wc -l /tmp/magpie_develop_ro/config/default.cfg    -> 2425 (line 225 in range)
$ read default.cfg:225
225: cfg$gms$sm_fix_SSP2 <- 2025
224: # Year until which all parameters are fixed to SSP2 values
```
=> file_evidence line CONTAINS the claimed identifier `sm_fix_SSP2` and its value is **2025**. citation_ok = TRUE. The "typically 2015" in the doc is wrong by 10 years.

Doc-internal code citations (also validated, since the fix leaves them in place):
- Active M55 realization = `ipcc2006_aug16` (default.cfg:1593 `cfg$gms$awms <- "ipcc2006_aug16"`). NOTE: the only other realization is `off` — there is NO `threepools_oct16` in M55; the auditor never cited a wrong realization here (the proposed fix touches only default.cfg + prose).
- `/tmp/magpie_develop_ro/modules/55_awms/ipcc2006_aug16/presolve.gms` EXISTS, 26 lines (so `:19`, `:20`, `:23-24`, `:25` all in range).
- presolve.gms:19 = `if(m_year(t) <= sm_fix_SSP2,`  (the gate)
- presolve.gms:20 = `ic55_awms_shr(i,kli,awms_conf) = f55_awms_shr(t,i,"ssp2",kli,awms_conf);` (SSP2 baseline assignment, historical branch) — matches doc line 292's "Fixed at SSP2 baseline (`presolve.gms:20`)".

### STEP B — Classify

class = **other**. This is a value/prose claim (a parameter's default numeric value embedded in a parenthetical), not a consumer_set / producer_declaration / realization_structure claim. Per protocol, class=other => verdict NOT_REVIEWABLE for the adversarial set-rederivation step, BUT the underlying value claim is mechanically checkable and I checked it (Step A): the auditor is correct.

### STEP C — Adjudicate

- Citation validated (Step A). The substantive claim ("default is 2025, not 2015") reproduces exactly against default.cfg:225.
- `sm_fix_SSP2` genuinely gates the historical-vs-future branch: `grep -rn "sm_fix_SSP2" .../55_awms/ipcc2006_aug16/` returns exactly ONE hit, presolve.gms:19 (isolated command, no chaining). No cross-realization confabulation: the parameter is in the ACTIVE realization, and there is no sibling realization that could host a different structure (only `off`, which has no such branch by name).
- Fix scope confirmed: read module_55.md:380-386. Line 381 = "**Historical calibration** (≤ `sm_fix_SSP2`):" — NO explicit year present, so it correctly needs no change. The fix correctly targets ONLY line 292. (Also note line 381's sibling line 382 cites presolve.gms:20 and line 383 cites presolve.gms:21 — both in range and correct; not part of the fix.)

**Verdict: UPHELD.** The auditor's value claim, file citation, gate attribution, and fix scoping all reproduce. Apply the fix verbatim: on module_55.md:292 replace "typically 2015" with "2025 by default". No other edits.

corrected_set: "" (no correction needed; fix as proposed).
