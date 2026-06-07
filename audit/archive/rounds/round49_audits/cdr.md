# Audit Report: CDR (Circular Dependency — TC/Yield/Production cluster, M13↔M14)

**Question**: Pick one documented circular dependency in the TC/yield/production cluster (M13, M14, M17). Per `circular_dependency_resolution.md`, what creates the cycle and how is it resolved (presolve fix / lagged pcm_ / simultaneous NLP)? Name variables + mechanism, verify against presolve/postsolve/equations code. Cite file:line.

**Anchor doc**: `cross_module/circular_dependency_resolution.md` §3.1 (Cycle 1 / Production-Yield-Livestock Triangle).

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

---

## Ground-truth setup (develop worktree `/tmp/magpie_develop_ro`)

Defaults (`config/default.cfg`):
- `cfg$gms$tc <- "endo_jan22"`  ✓
- `cfg$gms$yields <- "managementcalib_aug19"`  ✓
- `cfg$gms$production <- "flexreg_apr16"`  ✓

Realization dirs confirmed via `ls`: `13_tc/{endo_jan22,exo,input}`, `14_yields/{managementcalib_aug19,input}`, `17_production/flexreg_apr16`. The answer scoped explicitly to `endo_jan22` + `managementcalib_aug19` (both default) — MANDATE 8 satisfied, M2 pass.

---

## Verified Claims (correct)

1. **M13→M14 crop link = live `vm_tau`.** `q14_yield_crop(j2,kcr,w)` reads `vm_tau(j2,"crop")`.
   - Code: `modules/14_yields/managementcalib_aug19/equations.gms:14-16` — quote is verbatim, line range exact.
   - `vm_tau` produced by `q13_tau` at `modules/13_tc/endo_jan22/equations.gms:52-53` — quote verbatim, line range exact.

2. **Core resolution claim — crop cycle is a SIMULTANEOUS NLP, not a presolve fix.** VERIFIED.
   - `vm_tau` is a live `positive variable` (`endo_jan22/declarations.gms:13`).
   - In `endo_jan22/presolve.gms:76`, `vm_tau.l(...)` is set as a STARTING VALUE (`.l`), and only inside the `if(ord(t)=1)` block (lines 73-77); never `.fx`. So `vm_tau` is endogenous in every solve. The answer's claim "No presolve fixed value breaks this link. `vm_tau` and `vm_yld` are both live variables in the solve" is correct.
   - Contrast: the NON-default `13_tc/exo` realization DOES `vm_tau.fx` (`exo/presolve.gms:61`). The answer correctly stayed within `endo_jan22`, avoiding the cross-realization trap (MANDATE 19).

3. **M13→M14 pasture link = LAGGED `pcm_tau`.** VERIFIED.
   - `q14_yield_past` reads `pcm_tau(j2,"crop")` at `equations.gms:35-39` (line 39 specifically) — quote verbatim.
   - `pcm_tau` updated in M13 postsolve: `pcm_tau(j, tautype) = vm_tau.l(j, tautype);` at `modules/13_tc/endo_jan22/postsolve.gms:16` — answer's paraphrase `pcm_tau = vm_tau.l` accurate, line exact.

4. **`vm_tau` consumer set.** Whole-tree grep of BOTH `vm_tau(` and `vm_tau.` (MANDATE 20): the only equation-form consumer outside M13's own producing equation is M14 `q14_yield_crop`. The answer did NOT over-claim M17 or M38 as `vm_tau` consumers (module_13.md:155,372 also state M38 is only a transitive consumer via `vm_yld`→`vm_prod`). MANDATEs 13/17/18 satisfied.

5. **nl_fix demoted correctly.** `nl_fix.gms` exists in M14; `nl_fix.gms:10` does `vm_yld.fx(...) = ... vm_tau.l(h,"crop") ...`, and `nl_release.gms` re-frees `vm_yld` bounds. The answer's framing — "`nl_fix.gms` fixes `vm_yld` from a previous solve's `vm_tau.l` but is an NLP warm-start device, not the primary cycle-breaker" — is accurate and matches `module_14.md:870-877`. This is the subtlest correct call in the answer (a warm-start prep-solve does temporarily fix `vm_yld`, but it is not the recursive-dynamic cycle-breaker).

6. **Bidirectional within-solve coupling is real.** `vm_tech_cost` (the τ investment cost) enters the objective at `modules/11_costs/default/equations.gms:22`; `vm_yld` flows to production via M30/M31 (`vm_yld` consumers grep → 30_croparea, 31_past). The land-saving benefit of τ is thus priced in the same solve. The summary-table row "M14→M13 (crop): vm_yld prices τ via land demand in objective" is an economic-coupling description, NOT a false claim that M13 reads `vm_yld` directly (it doesn't). Framing is precise.

7. **All identifiers exist** (declarations checked): `v13_tau_core`, `v13_tau_consv`, `p13_cropland_consv_shr`, `vm_tau`, `pcm_tau`, `fm_tau1995`, `i14_yields_calib`. No fabricated names (MANDATE 7).

8. **Mechanical checks**: M1 pass (full-path file:line citations), M2 pass (default realizations stated), M3 pass (prefixes valid), M4/M5 pass (🟡 badge + doc cites), M6 pass (closing source statement).

---

## Bugs Found

None (no Critical, Major, Minor, or Informational).

### Non-bug nitpicks (explicitly NOT scored)
- The answer lists M13's solve-side equations as `q13_cost_tc`, `q13_tech_cost`, `q13_tau`, omitting `q13_tech_cost_sum` (which actually produces the interface `vm_tech_cost`) and `q13_tau_consv`. The answer framed this as an illustrative "the solver receives ... simultaneously", not an exhaustive list, and did NOT misattribute which equation produces `vm_tech_cost`. Descriptive incompleteness of an illustration → no trigger fires.

---

## Latent doc bugs (rubric §1.5)

None. The load-bearing doc claims were cross-checked against code and all hold:
- `circular_dependency_resolution.md` §3.1 (anchor) — its three citations (`equations.gms:14-16`, `equations.gms:35-39`, `postsolve.gms:16`) all resolve to the claimed content in current develop.
- `module_14.md:43,85,111,870-877` — q14_yield_crop/q14_yield_past line ranges, the "pcm_tau = previous timestep (not current!)" note, and the nl_fix description all match code.
- `module_13.md:98-103` (q13_tau @ equations.gms:52-53), `:152` (vm_tau consumer = M14, declared declarations.gms:13), `:294-301` (pcm_tau = vm_tau.l carryover) — all match code.

The doc set this answer relied on is in good shape for the M13↔M14 sub-cycle.

---

## Missing Nuances (minor, not penalized)

- The answer could have noted that `vm_yld`'s direct consumers are M30 (croparea) and M31 (pasture), with M17 receiving production only downstream of M30 — clarifying why M17 itself reads neither `vm_tau` nor `vm_yld` (grep of `17_production/flexreg_apr16/*.gms` returns empty for both). The answer's choice to frame the cycle as M13↔M14 (rather than dragging M17 in as a direct reader) is the correct, defensible reading of the question, so this is an enhancement, not a gap.

---

## Summary

A model answer. It correctly identified the documented M13↔M14 sub-cycle, named the exact interface variables (`vm_tau` live for crops; `pcm_tau` lagged for pasture), and got the resolution mechanism exactly right on the highest-risk axis: crops are resolved by simultaneous NLP (verified `vm_tau` is `.l`-seeded but never `.fx`'d in the default `endo_jan22`), pasture by a previous-timestep lagged parameter updated in postsolve. It also correctly demoted the `nl_fix`/`nl_release` warm-start to a solver device rather than the cycle-breaker — the single most confabulation-prone point in this topic. All quoted equations are verbatim and all line citations resolve in current develop. Score 10/10; no answer bugs, no latent doc bugs.
