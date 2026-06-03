# Audit Report: G1 (Module 14 Yields — Default Realization + Equation List)

**Round:** 42 | **Regression anchor:** G1 (stability anchor) | **Auditor:** Opus 4.8
**Ground truth:** develop @ HEAD `ee98739fd` (clean working tree for tracked files)
**Answer audited:** `audit/archive/rounds/round42_answers/g1_answer.md`

---

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: **false**

---

## Mechanical Checks (M1–M6)

| Check | Result | Evidence |
|---|---|---|
| **M1** File:line citations present | ✅ PASS | Cites `config/default.cfg:354`, `equations.gms:14-20`, `equations.gms:24-39`, `module_14_notes.md:13` |
| **M2** Active realization stated + matched to default | ✅ PASS | States `managementcalib_aug19` is default AND the only realization; confirms via config |
| **M3** Variable prefixes valid | ✅ PASS | `vm_yld`, `vm_tau`, `fm_tau1995`, `pcm_tau`, `pm_past_mngmnt_factor`, `i14_yields_calib`, `s14_yld_past_switch` — all prefixes consistent with code |
| **M4** Epistemic badges present | ✅ PASS | 🟡 documented / 🟢 for config line read this session |
| **M5** Confidence tier matches verification depth | ✅ PASS | Honest: tags doc-derived claims 🟡, the directly-read config line 🟢, and explicitly states `.gms` not opened per task constraint |
| **M6** Closing source statement | ✅ PASS | Closing "Source Statement" block lists module_14.md, module_14_notes.md:13, default.cfg:354 |

All 6 mechanical checks pass.

---

## Verified Claims (correct)

1. **Default realization = `managementcalib_aug19`** — VERIFIED.
   `config/default.cfg:354`: `cfg$gms$yields <- "managementcalib_aug19"          # def = managementcalib_aug19`. Answer quotes this line verbatim.

2. **It is the sole realization** — VERIFIED.
   `ls modules/14_yields/` → `managementcalib_aug19/`, `input/` (input-data dir, not a realization), `module.gms`. Only one realization directory. `module.gms:31` has a single `$Ifi "%yields%" == "managementcalib_aug19"` include — no other realization branch.

3. **Exactly 2 equations: `q14_yield_crop` and `q14_yield_past`** — VERIFIED.
   `modules/14_yields/managementcalib_aug19/equations.gms` defines exactly these two. `grep '^[ ]*q14_' declarations.gms` → 2 lines. **No invented `q14_yieldcalib`** (the R22-corrected non-existent equation) appears. Answer explicitly states "exactly 2 equations."

4. **`q14_yield_crop` body** — VERIFIED verbatim against `equations.gms:14-16`:
   ```
   q14_yield_crop(j2,kcr,w) ..
    vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                            vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
   ```
   Answer's snippet matches character-for-character. Mechanism description (calibrated baseline × current-τ / 1995-baseline-τ ratio; vm_tau at cluster j, fm_tau1995 at super-region h) is correct.

5. **`q14_yield_past` body** — VERIFIED verbatim against `equations.gms:35-39`:
   ```
   q14_yield_past(j2,w) ..
    vm_yld(j2,"pasture",w) =e=
    sum(ct,(i14_yields_calib(ct,j2,"pasture",w))
    * sum(cell(i2,j2),pm_past_mngmnt_factor(ct,i2)))
    * (1 + s14_yld_past_switch*(sum((cell(i2,j2), supreg(h2,i2)), pcm_tau(j2, "crop")/fm_tau1995(h2)) - 1));
   ```
   Answer's snippet matches exactly. Mechanism description correct on all three points:
   - exogenous pasture management factor `pm_past_mngmnt_factor` (from Module 70) — confirmed in `equations.gms:26-28` prose and equation line 38;
   - crop→pasture spillover using the **previous** timestep's τ (`pcm_tau`, not current `vm_tau`) — confirmed line 39;
   - spillover scaled by `s14_yld_past_switch` — confirmed line 39.

6. **`s14_yld_past_switch` default = 0.25** — VERIFIED.
   `modules/14_yields/managementcalib_aug19/input.gms:20`: `s14_yld_past_switch ... / 0.25 /`. Answer states "default 0.25" — exact.

7. **`biocorrect` realization removed in 2021, commit `cc84ae5e1`** — VERIFIED.
   `git log` → `cc84ae5e1 Update to new revision and clean up old realizations`. Commit hash and characterization correct.

---

## Bugs Found

**None.** No Critical, Major, Minor, or Informational bugs.

---

## Citation-precision note (not a bug)

The answer cites the equation ranges as `q14_yield_crop` → "14-20 (core 14-16)" and `q14_yield_past` → "24-39 (core 35-39)". The wide ranges include the `*'` doc-comment headers (lines 22-33 for pasture), and the answer EXPLICITLY disambiguates with "core expression at lines 35-39" / "core 14-16", which is exactly where the equation statements live. This is accurate range-with-disambiguation, not citation drift (rubric §1 Major "citation drift to adjacent content" does NOT fire — the cited core lines hold the actual equation). No deduction.

---

## Missing Nuances

Negligible. Two optional enrichments a maximal answer might add, neither a defect:
- `nl_fix.gms:11` contains a `vm_yld.fx(...)` pasture fixing statement that mirrors `q14_yield_past` algebraically (used in the NLP fix step). It is not an `equations.gms` equation, so its omission is correct for this question's scope.
- The answer's note that `s14_yld_past_switch` ranges 0–1 (0 = no spillover, 1 = full) is supported by `equations.gms:31-33` prose; the answer captured the default (0.25) correctly.

---

## Drift Assessment (G1 regression anchor)

- Default realization expected `managementcalib_aug19` → **matches** code (default.cfg:354).
- Equation list expected exactly 2 (`q14_yield_crop`, `q14_yield_past`) → **matches** code.
- No `q14_yieldcalib` regression (R22 correction held).

**drift_observed = false.** Ground truth unchanged since the anchor was set; answer tracks it exactly.

---

## Summary

A clean 10/10 on the G1 stability anchor. The answer correctly identifies `managementcalib_aug19` as both the default and sole realization (verified against `default.cfg:354` and `ls modules/14_yields/`), lists exactly the two equations that exist, reproduces both equation bodies verbatim, and describes the mechanisms (tau-ratio crop scaling; pasture management factor; 25% crop→pasture spillover on previous-timestep `pcm_tau`) faithfully. The `s14_yld_past_switch` default (0.25) and the `biocorrect`-removal commit (`cc84ae5e1`) are both confirmed. The R22-corrected non-existent `q14_yieldcalib` does not reappear. All 6 mechanical checks pass. No doc bugs surfaced — the load-bearing doc claims the answer relied on (module_14.md equation count = 2; module_14_notes.md:13 only-realization warning) are correct versus code, so no `doc_error_answerer_beat_it` is recorded.

**DOC BUGS TO FIX:** none.
