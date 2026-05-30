# Audit Report: G1 (Module 14 yields — default realization + equations)

**Round**: 33 | **Anchor type**: G1 calibration/regression (stability anchor) | **Date**: 2026-05-30
**Ground truth source**: `/tmp/magpie_develop_ro` (read-only develop clone); `config/default.cfg`

## Overall Verdict: ACCURATE
## Accuracy Score: 9/10
## Drift observed: NO

---

## Ground-truth verification (this session, against /tmp/magpie_develop_ro)

| Claim | Verified? | Evidence |
|---|---|---|
| Default realization `managementcalib_aug19` | ✅ | `config/default.cfg`: `cfg$gms$yields <- "managementcalib_aug19"  # def = managementcalib_aug19` |
| Only realization (no others present) | ✅ | `ls modules/14_yields/*/` → only `managementcalib_aug19/` + `input/` |
| Exactly 2 equations | ✅ | `grep -n 'q14_' .../equations.gms` → only `q14_yield_crop` (L14), `q14_yield_past` (L35) |
| `q14_yieldcalib` does NOT exist | ✅ | grep exit 1 + `rg` explicit not-found across all modules (R22 correction holds) |
| `q14_yield_crop` scales `i14_yields_calib` by `vm_tau(,"crop")/fm_tau1995` | ✅ | `equations.gms:14-16` |
| `q14_yield_past` uses `pm_past_mngmnt_factor` + `pcm_tau` (lagged) + spillover switch | ✅ | `equations.gms:35-39` |
| `s14_yld_past_switch = 0.25` (default) | ✅ | `input.gms:20`: `... / 0.25 /` |
| Output var `vm_yld` | ✅ | present in both equations |
| `biocorrect` realization existed & was removed | ◑ partial | Not in current tree (grep exit 1). Commit `cc84ae5e1` "...clean up old realizations" confirms removal of old realization dir(s). Exact name `biocorrect` and year "2021" not independently pinned, but substance (only managementcalib remains) is correct. Non-load-bearing aside. |

Positive control: `grep -c vm_yld .../equations.gms` → 2 (search works in dir before any absence call).

## Verified Claims (correct)
- Default realization, sole realization, equation count (2), both equation names, all cited variable names (`i14_yields_calib`, `vm_tau`, `fm_tau1995`, `pm_past_mngmnt_factor`, `pcm_tau`, `vm_yld`), the spillover-switch default (0.25), the lagged-tau (`pcm_tau` = previous timestep) nuance for pasture. All confirmed against code this session.

## Bugs Found

- **Bug ID**: G1-B1
- **Severity**: Minor
- **Class**: 10 (stale/imprecise file:line citation)
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things."
- **Claim in answer**: `q14_yield_past` (`equations.gms:24-39`).
- **Reality in code**: equation header is `equations.gms:35`; body 35-39. Line 24 is an explanatory comment (`*' factor ...`), not the equation. The cited range DOES enclose the equation and the end-line (39) is exact; the start point (24) lands in the equation's own comment block.
- **File evidence**: `modules/14_yields/managementcalib_aug19/equations.gms:35-39` (eqn); :22-34 (comments).
- **Tier note**: Between Minor (off-by-few, adjacent comments describe THIS equation) and Major (drift to different content). Range encloses the correct equation → tie-breaker §1 pulls to Minor.

### Informational (not scored)
- `q14_yield_crop` cited as `:14-20`; actual eqn body 14-16 (line 14 = correct header; 18-20 are trailing comments). Start point correct, range over-extends. Informational.

## Mechanical checks
M1 file:line present ✅ | M2 active realization stated (sole = default) ✅ | M3 prefixes valid ✅ | M4 badges: minimal but "Source:" footer present | M6 closing source statement ✅ (module_14.md + notes).

## Missing nuances
None load-bearing. Answer correctly captures lagged-tau, exogenous management factor, and the crop→pasture spillover. Sourced to docs (module_14.md), but every load-bearing claim independently confirms against code.

## Latent doc bugs
None detected. The answer's facts match code; no `doc_error_answerer_beat_it` triggered (no evidence module_14.md carries a wrong load-bearing claim that the answer relied on — the equation list/count/names are all correct).

## Summary
Anchor is STABLE. Default realization, equation count (2), and both equation names are exactly correct; the R22 correction (no `q14_yieldcalib`) holds and the answer respects it. One Minor citation imprecision (pasture equation range starts 11 lines early, in its own comment block, but encloses the equation; end-line exact). No Critical/Major issues. Score 9/10. drift_observed=false.
