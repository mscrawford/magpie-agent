# Round 50 Verification — module_51.md (nremis bugs)

Verifier: adversarial (Opus 4.8 1M). Ground truth: `/tmp/magpie_develop_ro` @ `ee98739fd`
(same HEAD as working tree). Default realizations confirmed: module 51 `rescaled_jan21`
(default.cfg:1550), module 50 `macceff_aug22` (1479), module 55 `ipcc2006_aug16` (1593),
module 56 `price_aug22` (1613).

---

## B1 — `m51-nremis-B1` — UPHELD (Major)

**Claim**: doc line 229 mis-files `vm_manure_recycling(i,"nr")` under "From Module 50
(NR Soil Budget)". True source (declarer + populator) is Module 55; Module 50 only READS
it on an RHS, exactly as Module 51 does. Fix: move bullet to the "From Module 55 (AWMS)"
block (after lines 237-239).

**Class**: producer_declaration (MANDATE 18 DECLARED-vs-POPULATED-vs-READ; bug class 15).

### STEP A — Mechanical citation check (citation_ok = TRUE)
```
test -f .../55_awms/ipcc2006_aug16/declarations.gms   -> EXISTS, 52 lines
test -f .../55_awms/ipcc2006_aug16/equations.gms      -> EXISTS, 87 lines
test -f .../50_nr_soil_budget/macceff_aug22/equations.gms -> EXISTS, 97 lines
test -f .../56_ghg_policy/price_aug22/sets.gms        -> EXISTS, 214 lines

declarations.gms:21  =>  vm_manure_recycling(i, npk)   ... (DECLARED)         [in range]
equations.gms:84     =>  vm_manure_recycling(i2,npk) =e=  (POPULATED LHS)     [in range]
                          (heads eq q55_manure_recycling at :83)
50 .../equations.gms:27 => + vm_manure_recycling(i2,"nr")  (READ on RHS)      [in range]
                          (summand inside q50_nr_inputs at :22; leading '+' => RHS)
```
All three file_evidence citations exist, are in range, and contain the claimed token.
Proposed-fix has no new file:line (re-uses doc-relative `equations.gms:25`).

### STEP C — Independent re-derivation of the producer/reader set
Greped BOTH `vm_manure_recycling(` and `vm_manure_recycling.` across all of
`/tmp/magpie_develop_ro/modules/` (rg, isolated). Positive control: the paren-grep
returns the known-present sibling lines, proving the search works in-tree.

DECLARED (declarations.gms) — **Module 55 ONLY**:
- 55_awms/ipcc2006_aug16/declarations.gms:21  (default)
- 55_awms/off/declarations.gms:11             (sibling `off` realization)
- ZERO declarations in Module 50 (or anywhere else).

POPULATED (LHS `=e=` / `.fx`) — **Module 55 ONLY**:
- 55_awms/ipcc2006_aug16/equations.gms:84  `vm_manure_recycling(i2,npk) =e=`
- 55_awms/off/preloop.gms:9  `vm_manure_recycling.fx(i, npk)=0;`  (off fixes to 0)

READ (RHS) — Modules 50 and 51:
- 50_nr_soil_budget/macceff_aug22/equations.gms:27  `+ vm_manure_recycling(i2,"nr")`
- 51_nitrogen/rescaled_jan21/equations.gms:25       `vm_manure_recycling(i2,"nr")`
  (this is the variable the doc Inputs section is documenting)

Solution-level `.l/.lo/.up/.m` reads exist only in Module 55's own postsolve (own var
readback), not in Module 50 — so no hidden Module-50 producer role via attributes.

**Verdict**: Module 50 is NOT a producer; it is a co-reader on equal footing with
Module 51. The variable's source is unambiguously Module 55. The doc's own line 40
("declared by Module 55 AWMS") and the line 455 Upstream-Dependencies table (lists
`vm_manure_recycling` under Module 55) already get this right — only the Inputs section
misfiles it. **UPHELD.**

**Fix is safe**: destination block lines 237-239 ("From Module 55 (AWMS)") already lists
`vm_manure_confinement` and `vm_manure`, both genuine Module-55 outputs; adding
`vm_manure_recycling` there is internally consistent. Keeping the doc-relative
`(equations.gms:25)` is correct (51_nitrogen/rescaled_jan21/equations.gms:25 confirmed to
reference the variable). corrected_set: source = Module 55 (declarer+populator); Module 50
= reader only.

---

## B2 — `m51-nremis-B2` — CORRECTED (Minor)

**Claim**: doc line 253 cites `(Module 56 sets.gms,196)` for `n2o_n_indirect`, but line
196 is `nh3_n, no2_n,`. Member sits at 195 (n_pollutants subset). Off-by-one.

**Class**: other (stale/imprecise file:line citation, class 10).

### STEP A — Mechanical citation check (citation_ok = TRUE)
```
test -f .../56_ghg_policy/price_aug22/sets.gms  -> EXISTS, 214 lines  (price_aug22 = default)
sets.gms:190 => "   n2o_n_direct, n2o_n_indirect,"   (pollutants set; contains token)
sets.gms:195 => "   / n2o_n_direct,n2o_n_indirect,"  (n_pollutants subset; contains token)
sets.gms:196 => "   nh3_n, no2_n,"                    (does NOT contain n2o_n_indirect)
positive control grep 'n2o_n_indirect' sets.gms -> 176, 190, 195  (search works)
```
Proposed-fix target line 195 exists, in range, and CONTAINS `n2o_n_indirect`. The
auditor's reality claim (196 = `nh3_n, no2_n,`; token at 195/190) reproduces exactly.

### Adjudication
The doc's current `196` is wrong (one past the member). The fix to `195` is mechanically
valid. Note line 190 (the `pollutants` set) also contains the token and is the more
canonical "first declaration as taxable pollutant" site; 195 is the `n_pollutants` subset.
Either is defensible and the surrounding doc context (line 251-253) lists `pollutants`
members, so 190 would be marginally more consistent — but 195 is what the auditor proposed,
contains the token, and is correct. I record corrected_set as "195 (or 190); both contain
the token; doc's 196 is off-by-one" and leave the final pick to the fixer. **CORRECTED.**

---

## Summary

| Bug | Class | citation_ok | Verdict |
|-----|-------|-------------|---------|
| m51-nremis-B1 | producer_declaration | true | UPHELD |
| m51-nremis-B2 | other | true | CORRECTED (-> sets.gms:195; 190 also valid) |

Both auditor evidence sets reproduced mechanically. No confabulation detected. No
cross-realization phantom (verified `off` sibling separately; it only strengthens B1 by
adding a second Module-55 declaration site and the `.fx` zero-fix).
