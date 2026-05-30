## Audit Report: G1 (Module 14 yields — default realization + equation list)

**Round**: 38 (calibration anchor / regression question)
**Date**: 2026-05-30
**Ground truth source**: `/tmp/magpie_develop_ro/config/default.cfg:354`, `/tmp/magpie_develop_ro/modules/14_yields/managementcalib_aug19/{equations,declarations,input}.gms`

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10
### Drift observed: NO

---

### Verified Claims (correct)

| Claim | Code evidence |
|---|---|
| Default realization `managementcalib_aug19` | `config/default.cfg:354`: `cfg$gms$yields <- "managementcalib_aug19"  # def = managementcalib_aug19` |
| Exactly 2 equations defined | `declarations.gms:30-31` declares `q14_yield_crop`, `q14_yield_past`; `equations.gms:14,35` defines both. No `q14_yieldcalib` (rubric's known trap — absent, confirmed). |
| `q14_yield_crop`: `i14_yields_calib` × `vm_tau(j,"crop")` / `fm_tau1995(h)` → `vm_yld(j,kcr,w)` tDM/ha/yr | `equations.gms:15-16`: `vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) * vm_tau(j2,"crop") / sum((cell(i2,j2),supreg(h2,i2)),fm_tau1995(h2))`; units per `declarations.gms:30` |
| `q14_yield_past`: calibrated baseline × `pm_past_mngmnt_factor`, plus spillover using **previous-step** `pcm_tau` (NOT `vm_tau`), weighted by `s14_yld_past_switch` | `equations.gms:35-39`: confirms `pm_past_mngmnt_factor(ct,i2)` scaling and `pcm_tau(j2,"crop")` (previous tau). Correct and subtle distinction. |
| `s14_yld_past_switch` default 0.25 | `input.gms:20`: `/ 0.25 /`; `config/default.cfg:366`: `# def = 0.25`. Both confirm. |

Positive control: `grep q14_` in the realization dir returns only `q14_yield_crop`/`q14_yield_past` (+ their `oq14_*` output-parameter twins, which are postsolve-populated reporting params, not model equations). Search proven to work in-dir.

### Bugs Found
None.

### Notes / sub-Minor observations (no deduction)

- **Line range for `q14_yield_past` (cited 24-39)**: the equation *statement* begins at `equations.gms:35`; lines 24-33 are the preceding `*'` comment block. The cited 24-39 range is a superset that encloses the equation plus its doc comments — it does NOT point a reader at wrong content (cf. the crop equation cited 14-20, where 14-16 is the equation and 18-20 trailing comments; same convention). Below Minor (the Minor anchor is "off-by-few citation where adjacent lines say similar things"; a superset range that contains the equation is strictly less misleading). Informational at most; not deducted.
- **Index-label simplification** (`j` for `j2`, `h` for `h2`): the answer uses the declaration-level labels (`declarations.gms:30` uses `j`,`kcr`,`w`) rather than the equation-domain aliases (`j2`,`h2`). Standard prose simplification, matches the doc's own convention. Not a bug.

### Mechanical checks (indicators, not bugs)

| Check | Result |
|---|---|
| M1 file:line citations present | PASS (`equations.gms:14-20`, `:24-39`) |
| M2 active realization stated + default confirmed | PASS |
| M3 variable prefixes valid | PASS (`vm_`,`pm_`,`fm_`,`pcm_`,`i14_`,`s14_`) |
| M4 epistemic badges (🟢/🟡) | FAIL — no badges on claims (indicator only) |
| M5 confidence tier matches depth | N/A (no badges) |
| M6 closing source statement | PARTIAL — cites `module_14.md` sections + answer-file path, but not the canonical "Based on / Verified against" phrasing. Substance present. |

M4/M6 are mechanical indicators per rubric §2 ("Failures are NOT bugs"); they do not enter the severity-weighted score. They flag that the answer's epistemic-marker hygiene is loose, but zero content bugs resulted.

### Summary

The answer matches the expected ground-truth summary on every load-bearing fact: correct default realization, correct equation count (exactly 2), no phantom `q14_yieldcalib`, correct mechanism for both equations including the subtle `pcm_tau` (previous-step) vs `vm_tau` (current-step) distinction in the pasture equation, and correct `s14_yld_past_switch = 0.25` default. The only blemishes are a loose-but-enclosing line range on the pasture equation and absent epistemic badges — neither is a scoring bug. Anchor is stable; no drift. Score 10/10.

raw_severity_weighted = 4(0) + 2(0) + 1(0) = 0 → score = max(0, 10 - 0) = 10.
