## Audit Report: G1 (Module 14 yields — default realization + equations list)

**Round**: 31 | **Date**: 2026-05-30 | **Type**: calibration anchor (regression)
**Auditor**: Opus 4.8 (1M)
**Ground-truth source**: `/tmp/magpie_develop_ro` (read-only develop clone)

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10
### Drift observed: NO

---

### Verified Claims (all correct)

| Claim in answer | Verification | Evidence |
|---|---|---|
| Default realization `managementcalib_aug19` | ✓ | `config/default.cfg:354` → `cfg$gms$yields <- "managementcalib_aug19"` |
| It is the only realization | ✓ | `ls modules/14_yields/*/` shows only `input/` + `managementcalib_aug19/` |
| Exactly 2 equations | ✓ | `grep -nE "^\s*q14_"` returns exactly 2 hits |
| `q14_yield_crop(j2,kcr,w)` | ✓ | `equations.gms:14` |
| `q14_yield_past(j2,w)` | ✓ | `equations.gms:35` |
| No phantom `q14_yieldcalib` | ✓ | `rg q14_yieldcalib modules/14_yields/` → NO_MATCH (+ positive control `vm_yld` matched, proving search works in dir) |
| Crop eq scales `i14_yields_calib` by `vm_tau(j2,"crop")/fm_tau1995` | ✓ | `equations.gms:15-16` |
| Pasture eq uses `pm_past_mngmnt_factor`, prev-step `pcm_tau`, `s14_yld_past_switch` | ✓ | `equations.gms:36-39` |
| `s14_yld_past_switch` default 0.25 | ✓ | `input.gms:20` → `/ 0.25 /` |
| Output `vm_yld` for both | ✓ | `equations.gms:15,36` |
| `i14_yields_calib` declared in M14 | ✓ | `declarations.gms:9` |

Positive control passed: `rg vm_yld` in the realization dir returned matches at lines 15 and 36, confirming the search tooling functions in that directory before concluding `q14_yieldcalib` is absent. Absence cross-checked with two methods (`rg` + direct `Read` of full file).

### Bugs Found
None of load-bearing significance.

### Citation-precision note (NOT scored as a bug)
The answer cites `equations.gms:14-20` (crop) and `equations.gms:24-39` (pasture). The tight equation-statement spans are 14-16 and 35-39 respectively; the answer's wider ranges bleed into the surrounding `*'` documentation comments (crop comment 18-20; pasture comment 24-34). Both range styles are present in the source doc `module_14.md` — the tight ones at lines 43/85, the wider ones at lines 79/120 — and the answer copied the wider variants. These are a defensible "equation + its inline `*'` doc comment" citation convention: the equation start-lines and names are exact, and both ranges encompass the correct equation. Per §1 tie-breaker (pick lower) and the absence of any content mismatch, this is Informational at most, not a Minor bug. Worth flagging for doc hygiene: `module_14.md` is internally inconsistent on these two citations (tight vs wide); harmonizing to 14-16 / 35-39 would remove the ambiguity, but this is a doc-cleanup nicety, not an answer error.

### Mechanical checks
- M1 file:line present ✓
- M2 realization stated (+ noted as only one) ✓
- M3 variable prefixes valid (`vm_`, `pm_`, `pcm_`, `fm_`, `i14_`, `s14_`) ✓
- M4/M5 epistemic tagging: answer sources `module_14.md` (🟡 documented) with "fully verified 2025-10-12" — acceptable; no overclaim of fresh code read ✓
- M6 closing source statement present ✓

### Missing Nuances
None material. The answer correctly highlights the load-bearing subtlety that the pasture equation uses **previous-step** τ (`pcm_tau`) rather than current `vm_tau`, and correctly states the spillover switch default (0.25). This is the one place an answerer commonly confabulates `vm_tau`; the answer got it right.

### Summary
Matches the expected ground-truth summary on every load-bearing point: default = only realization `managementcalib_aug19`; exactly 2 equations (`q14_yield_crop`, `q14_yield_past`); no phantom `q14_yieldcalib`. Anchor is STABLE. No drift. Score 10/10.
