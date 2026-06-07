# Round 50 Adversarial Verification — Data_Flow.md (drivers/yields/trade)

Verifier: Opus 4.8 (1M). Ground truth: `/tmp/magpie_develop_ro` (develop worktree).
Target doc: `core_docs/Data_Flow.md`.

---

## DF-B1 — q14_yield_crop formula sum-scope drift

**Class:** realization_structure (formula a specific realization's equation defines)
**Verdict: UPHELD** | citation_ok = true

### Step A — Mechanical citation check
```
test -f modules/14_yields/managementcalib_aug19/equations.gms  -> EXISTS
wc -l ...                                                        -> 39 lines (14-16 in range)
```
Read of lines 14-16 (verbatim):
```gams
q14_yield_crop(j2,kcr,w) ..
 vm_yld(j2,kcr,w) =e= sum(ct,i14_yields_calib(ct,j2,kcr,w)) *
                         vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));
```
Line contains the claimed token `q14_yield_crop`. Citation valid.

### Step C — Adjudication
Default yields realization confirmed: `config/default.cfg:354` → `cfg$gms$yields <- "managementcalib_aug19"`. So the cited realization IS the active one — formula claim is on-default.

- **Doc (Data_Flow.md:216-221)** shows: `... * sum((cell(i2,j2), supreg(h2,i2)), vm_tau(j2,"crop") / fm_tau1995(h2));`
  i.e. the `sum()` wraps the WHOLE ratio `vm_tau / fm_tau1995`.
- **Code (equations.gms:14-16)** shows: `... * vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2));`
  i.e. the `sum()` wraps ONLY the denominator `fm_tau1995`; `vm_tau(j2,"crop")` sits OUTSIDE the sum as the numerator.

These are mathematically different (numerator inside vs outside the regional sum). The proposed_fix string reproduces the code line exactly. The bug's narrative "commit 7af46385c" is not load-bearing — the fix is verified directly against the current line, not the commit.

**Conclusion:** UPHELD. Apply proposed_fix (replace doc 216-221 with the code formula; cite equations.gms:14-16).

---

## DF-B2 — v21_trade presented in Key Optimization Variables table without non-default caveat

**Class:** producer_declaration (which realization DECLARES v21_trade) + capability-vs-default (MANDATE 4)
**Verdict: UPHELD** | citation_ok = true

### Step A — Mechanical citation check
```
test -f modules/21_trade/selfsuff_reduced_bilateral22/declarations.gms -> EXISTS (62 lines; 23 in range)
test -f modules/21_trade/selfsuff_reduced/declarations.gms             -> EXISTS (56 lines; 18-20 in range)
```
- bilateral22/declarations.gms:23 (verbatim): `v21_trade(i_ex,i_im,k_trade)  Bilateral trade flow ...` — contains claimed token `v21_trade`. Valid.
- selfsuff_reduced/declarations.gms:18-20: `v21_excess_dem(k_trade)`, `v21_excess_prod(h,k_trade)`, `v21_import_for_feasibility(h,k_trade)` — contains the claimed alternative tokens. Valid.

### Step C — Adjudication (independent re-derivation; producer/declaration + default)
Default trade realization: `config/default.cfg:650` → `cfg$gms$trade <- "selfsuff_reduced"`. Confirmed default is NOT bilateral22.

Whole-tree grep for `v21_trade` — BOTH forms + second method + positive control:
- `rg 'v21_trade\(' modules/` → all hits in `selfsuff_reduced_bilateral22/` only (declarations:23, equations:32/49/62/73/83, output decl ov21_trade:46).
- `rg 'v21_trade\.' modules/` (solution-level .l/.lo/.up/.m) → all hits in bilateral22 (postsolve:10/26/42/58) + one comment in equations:15. None elsewhere.
- Second method `grep -rn 'v21_trade' modules/ | grep -v _bilateral22` → `NO_MATCHES_OUTSIDE_BILATERAL22`.
- **Positive control** in default dir `selfsuff_reduced/`:
  - `v21_excess_prod` PRESENT (declarations:19, equation LHS:57, postsolve) — proves grep works in that dir.
  - `v21_excess_dem` PRESENT (declarations:18, equation LHS:48, postsolve).
  - `v21_trade` → `CONFIRMED_ABSENT_IN_DEFAULT`.

Trade realizations on disk: `exo/`, `input/`, `selfsuff_reduced/` (default), `selfsuff_reduced_bilateral22/`.

**Conclusion:** UPHELD. `v21_trade` is declared/populated ONLY in the non-default `selfsuff_reduced_bilateral22`; the default `selfsuff_reduced` uses `v21_excess_prod` / `v21_excess_dem` (and `v21_import_for_feasibility`). Listing `v21_trade` in the "Key Optimization Variables" table next to always-present vars (vm_land, vm_prod, vm_yld) with no caveat is a capability-vs-default error. Apply proposed_fix (annotate as non-default, or move to a labeled non-default note). Fix parenthetical naming `v21_excess_prod`/`v21_excess_dem` is accurate; no correction.

---

## Summary
| Bug | Class | citation_ok | Verdict |
|-----|-------|-------------|---------|
| DF-B1 | realization_structure | true | UPHELD |
| DF-B2 | producer_declaration | true | UPHELD |

Both fixes are safe to apply. No CITATION_FAILED, no confabulated cross-realization claims detected; both auditor claims reproduced mechanically with positive controls.
