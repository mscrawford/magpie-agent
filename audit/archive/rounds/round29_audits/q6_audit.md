## Audit Report: Q6 / G1 (Module 14 Yields — Default Realization and Equations)

**Round**: R29
**Regression anchor**: G1 (stability anchor)
**Worktree**: /tmp/magpie-develop-r29/ @ ee98739fd (verified HEAD matches)
**Auditor**: Opus adversarial pass

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10
### drift_observed: false

---

### Verified Claims (correct)

1. **Default realization = `managementcalib_aug19`** — CONFIRMED.
   - `config/default.cfg`: `cfg$gms$yields <- "managementcalib_aug19"          # def = managementcalib_aug19`
   - Realization dir exists: `modules/14_yields/managementcalib_aug19/` (only non-`input` realization dir present; `ls -d modules/14_yields/*/` → `input/`, `managementcalib_aug19/`).

2. **equations.gms defines EXACTLY 2 equations** — CONFIRMED.
   - `modules/14_yields/managementcalib_aug19/equations.gms` (39 lines, read in full) contains exactly two equation definitions:
     - `q14_yield_crop(j2,kcr,w) ..` at line 14
     - `q14_yield_past(j2,w) ..` at line 35
   - `grep -nE "^[ ]*q14_" equations.gms` → only lines 14 and 35.
   - Cross-check declarations.gms:29-32 `equations` block declares exactly `q14_yield_crop(j,kcr,w)` (line 30) and `q14_yield_past(j,w)` (line 31). The `oq14_yield_crop`/`oq14_yield_past` at lines 37-38 are R-section OUTPUT PARAMETERS (`parameters` block, not `equations`), correctly NOT counted as equations.

3. **No phantom `q14_yieldcalib`** — CONFIRMED ABSENT. This is the specific drift the R22 audit corrected (rubric §6 / §9 v1.1 note). The answer does NOT reintroduce it. No such identifier exists in equations.gms or declarations.gms.

4. **q14_yield_crop cited at `equations.gms:14-16`** — CONFIRMED EXACT. The equation body spans lines 14-16 verbatim:
   ```
   14:q14_yield_crop(j2,kcr,w) ..
   15: vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
   16:                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
   ```
   The quoted GAMS in the answer matches the worktree character-for-character.

5. **q14_yield_past cited at `equations.gms:35-39`** — CONFIRMED EXACT. The equation body spans lines 35-39 verbatim:
   ```
   35:q14_yield_past(j2,w) ..
   36: vm_yld(j2,"pasture",w) =e=
   37: sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
   38: * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
   39: * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
   ```
   The quoted GAMS in the answer matches the worktree character-for-character.

6. **`s14_yld_past_switch` default = 0.25, input.gms:20** — CONFIRMED EXACT.
   - `input.gms:20`: `s14_yld_past_switch  ... Spillover parameter ... (1)     / 0.25 /`

7. **`pcm_tau` (previous time-step τ) vs `vm_tau` (current τ) distinction** — CONFIRMED. q14_yield_crop (line 16) uses `vm_tau`; q14_yield_past (line 39) uses `pcm_tau`. The answer's "Key difference" callout is mechanically accurate per code.

8. **Variable-name fidelity** — all interface names checked against declarations: `vm_yld` (declarations.gms:26), `i14_yields_calib` (line 9), `vm_tau`/`fm_tau1995`/`pcm_tau` (used in equations, M13 interface), `pm_past_mngmnt_factor` (M70 interface). No confabulated names. Prefixes valid (M3 pass).

### Bugs Found

None. (0 Critical, 0 Major, 0 Minor, 0 Informational.)

### Mechanical Checks (§2)

- **M1** File:line citations present — PASS (`equations.gms:14-16`, `:35-39`, `input.gms:20`).
- **M2** Active realization stated — PASS (`managementcalib_aug19` named and matched to default explicitly).
- **M3** Variable prefixes valid — PASS.
- **M4** Epistemic badges present — PASS (🟢 config-verified, 🟡 documented in Sources block).
- **M5** Confidence tier matches depth — PASS (config 🟢 from grep; doc-derived line numbers tagged 🟡 with explicit "verify against current code" caveat).
- **M6** Closing source statement — PASS (Sources section: "Verified" config + "Documented" module_14.md).

### Missing Nuances (non-scoring)

- The answer carries two parenthetical alternate ranges sourced from `module_14.md`'s own footnotes: `:14-20` for q14_yield_crop and `:24-39` for q14_yield_past. These are NOT errors — they are supersets that include the adjacent `*'` explanatory comment blocks (lines 18-20 describe the crop calc; lines 24-33 describe the pasture calc/`s14_yld_past_switch`). The PRIMARY cited ranges (14-16, 35-39) are exact equation-body ranges. The alternates are clearly labeled as doc footnotes and would not mislead a careful reader. Below even Informational; recorded only for completeness.
- The answer pre-emptively flags that doc-sourced line numbers may drift (Note + verification command), which is the correct discipline for a 🟡-sourced citation.

### Latent doc bugs (§1.5)

None. Spot-check of the load-bearing doc claims the answer leaned on (module_14.md realization name, equation count, both equation names, the two line ranges, `s14_yld_past_switch=0.25`) all match the worktree code. No `doc_error_answerer_beat_it` to record — the doc and the code agree on every G1-relevant fact. (The R22 correction to remove `q14_yieldcalib` has held through R29.)

### Summary

Textbook-accurate G1 answer. Default realization `managementcalib_aug19` verified against config; exactly 2 equations (`q14_yield_crop`, `q14_yield_past`) verified against both equations.gms and the declarations.gms `equations` block; both line ranges exact; both formulas verbatim; `s14_yld_past_switch=0.25` exact; no phantom `q14_yieldcalib`; correct `pcm_tau`-vs-`vm_tau` mechanism. Zero bugs. The G1 stability anchor holds at 10/10 with no drift. Score 10/10.
