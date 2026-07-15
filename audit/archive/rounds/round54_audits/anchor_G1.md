# Audit Report: G1 (Module 14 yields — default realization + equations.gms)

**Round**: 54 (calibration anchor, stability)
**Auditor model**: Opus 4.8
**Date**: 2026-07-15

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: FALSE

---

## Ground truth verified this session (from /tmp/magpie_develop_ro)

1. **Default realization** — `/tmp/magpie_develop_ro/config/default.cfg:354`:
   `cfg$gms$yields <- "managementcalib_aug19"   # def = managementcalib_aug19`
   → default = `managementcalib_aug19`. CONFIRMED.

2. **Realization directories** — `modules/14_yields/` contains only `input/` and
   `managementcalib_aug19/`. `input/` is the shared input-data folder, not a
   realization. So `managementcalib_aug19` is the sole realization. CONFIRMED.

3. **equations.gms** (read in full, 40 lines) — exactly 2 equations DEFINED:
   - `q14_yield_crop(j2,kcr,w) ..` at line 14 (body lines 14-16)
   - `q14_yield_past(j2,w) ..`     at line 35 (body lines 35-39)
   No `q14_yieldcalib`. declarations.gms additionally declares reporting equations
   `oq14_yield_crop`/`oq14_yield_past` (o-prefixed outputs, NOT defined in
   equations.gms). CONFIRMED exactly 2 in equations.gms.

Positive control: rg matched `gms$yields` in default.cfg and `q14_` tokens in both
equations.gms and declarations.gms — search apparatus proven working in-tree.

---

## Verified Claims (all correct)

- Default realization `managementcalib_aug19` → matches default.cfg:354. ✓
- "Only realization; earlier biocorrect removed 2021" → directory listing shows only
  managementcalib_aug19; consistent (biocorrect commit hash not load-bearing, not chased). ✓
- Equation count = 2 → matches equations.gms and module_14.md:6/:1051. ✓
- `q14_yield_crop`, formula `vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(...)) *
  vm_tau(j2,"crop") / sum((cell(i2,j2),supreg(h2,i2)),fm_tau1995(h2));`
  → verbatim match to equations.gms:14-16. ✓
- `q14_yield_past` formula → verbatim match to equations.gms:35-39. ✓
- Citations `equations.gms:14-16` and `35-39` → exact. The alternate ranges the answer
  also reports (`14-20`, `24-39`) mirror the doc's broader `Citation:` fields
  (module_14.md:79/:120); both bracket the correct equation, neither misleads. ✓
- Correctly OMITS the historically mis-listed phantom `q14_yieldcalib`. ✓
- All variable prefixes valid (vm_yld, vm_tau, i14_yields_calib, pm_past_mngmnt_factor,
  s14_yld_past_switch, pcm_tau, fm_tau1995). ✓

## Latent doc-bug check (§1.5 mandate)
Answer was docs-only (module_14.md + module_14_notes.md; no .gms read). Cross-checked
the relied-upon doc against code: module_14.md:3 (realization), :6 (count 2), :43/:85
(File: 14-16 / 35-39), :1051 (2 equations verified) are ALL correct vs code. No
load-bearing doc error behind the correct answer. Nothing to record.

## Bugs Found
None (0 Critical, 0 Major, 0 Minor).

## Mechanical checks
- M1 file:line present — PASS (14-16, 35-39)
- M2 active realization stated — PASS (managementcalib_aug19, sole/default)
- M3 prefixes valid — PASS
- M4 per-claim emoji badges 🟢/🟡 — technically absent (answer uses prose disclosure
  "doc-stated, verbatim, not recomputed; no raw GAMS files read this session").
  Informational-tier stylistic item per §1 (weight 0); does NOT reduce score.
- M5 confidence tier matches depth — PASS (honestly flags documented-tier, claims no 🟢)
- M6 closing source statement — PASS ("Sources: module_14.md ...")

## Scoring
raw_severity_weighted = 4(0) + 2(0) + 1(0) = 0
score = max(0, 10 - 0) = **10**

## Drift assessment
Answer matches the expected summary on every load-bearing point: correct default
realization, correct equation count (2), correct equation names/formulas, phantom
`q14_yieldcalib` correctly absent, count reported not reconstructed. **No drift.**
The anchor is stable at 10.
