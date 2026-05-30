# Round 39 Doc Audit — reference/GAMS_Functions_Operations.md

**Auditor model**: Opus 4.8 (1M)
**Date**: 2026-05-30
**Ground truth**: official GAMS docs (gams.com/latest) for language semantics; `/tmp/magpie_develop_ro` for MAgPIE-convention/example claims.
**Pre-run advisory checked**: "GAMS built-in functions + string/set operations. Verify function names/semantics vs gams.com; verify any MAgPIE example vs develop." — VERIFIED below (one fabricated official quote found re: indexed operators; function names/semantics otherwise correct).

---

## Scope of load-bearing, code-checkable claims

This doc is a GAMS-language reference. The code-checkable surface is:
1. **MAgPIE file:line citations** (6 total): `core/macros.gms:18`, `core/macros.gms:16`, `modules/56_ghg_policy/price_aug22/preloop.gms:82`, `modules/10_land/landmatrix_dec18/equations.gms:32` (×2), `.../equations.gms:14`.
2. **MAgPIE variable/macro names** quoted in examples (`vm_land`, `pcm_land`, `vm_lu_transitions` / written as `v10_lu_transitions`, `m_growth_vegc`, `m_weightedmean`, `smax(t2, ord(t2)$(t_past(t2)))`).
3. **GAMS function names + semantics** (exp/log/log10/power/sqrt/sqr/abs/sign/round/floor/ceil/trunc/min/max/sin../mod/errorf/diag/sameas/ord/card).
4. **Quoted "Official GAMS Documentation" snippets** (must be verified verbatim against the cited gams.com pages).
5. **Logical/comparison operator tables**, smin/smax DNLP restriction.

Pure prose/advice (readability tips, "less common in MAgPIE", protection-pattern idioms) is skipped as not code-checkable.

---

## Verified-correct claims (high confidence)

- **`core/macros.gms:18` → `m_growth_vegc`**: CORRECT. Line 18 is `$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m;`. Doc quote matches (trailing `;` trivially omitted). Uses `exp()` as claimed.
- **`core/macros.gms:16` → `m_weightedmean`**: CORRECT. Line 16 is `$macro m_weightedmean(x,w,s) (sum(s,x*w)/sum(s,w))$(sum(s,w)>0) + 0$(sum(s,w)<=0);`. Doc quote matches; "returns 0 if total weight is zero" is accurate.
- **`modules/10_land/landmatrix_dec18/equations.gms:14`** → `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));`: CORRECT. Statement spans code lines 13-15; `:14` (the `=e=` line) is within range and content present. `vm_land` (declarations.gms:19) and `pcm_land` (declarations.gms:11) both real.
- **Realization names** `landmatrix_dec18` (module 10) and `price_aug22` (module 56): both exist (`ls`). Both are the sole/active realization of their module dir.
- **`smax(t2, ord(t2)$(t_past(t2)))`** (doc:596, uncited "MAgPIE example - Last historical timestep ordinal"): REAL — appears verbatim at `modules/70_livestock/fbask_jan16/presolve.gms:16` and `fbask_jan16_sticky/presolve.gms:16`. No citation given, so no drift risk. ACCURATE.
- **GAMS function names/semantics** (gams.com/latest/docs/UG_Parameters.html, Table 3):
  - `power(x,y)` "Y must be an integer" — CONFIRMED ("Returns x^Y, where Y must be an integer"). Doc lines 60, 75 correct.
  - `errorf(x)` = standard normal CDF Φ(x) — CONFIRMED ("Integral of the standard normal distribution from negative infinity to x").
  - `log10`, `sqr`, `trunc` (toward zero), `ceil`, `sign`, `mod(x,y)`, `round(x[,DECPL])` — all CONFIRMED present with matching descriptions.
  - `arctan2(y,x)` — doc calls it "Two-argument arc tangent"; GAMS calls it "Four-quadrant arctan". Benign simplification, NOT flagged (two-argument is true).
- **smin/smax DNLP restriction** (doc:611): quoted verbatim and CORRECT ("The indexed operations smin and smax may be used in equation definitions only if the corresponding model is of type DNLP.").
- **Logical operators** (doc 2.3: not/and/or/xor/imp/eqv) and **comparison operators** (doc 2.2: lt/le/eq/ne/ge/gt): all CONFIRMED against UG_CondExpr Table 1 & 2.
- **`ord` returns position, `card` returns count** (doc 3.2, 3.3): CONFIRMED (UG_OrderedSets).
- **Dollar operator for exceptions** (doc:672): CONFIRMED real on UG_CondExpr.
- **No short-circuit warning** (doc 2.5): UG_CondExpr does not address evaluation order, but the claim (GAMS evaluates both operands; `(x<>0 and y/x>10)` is unsafe) is correct, well-known GAMS behavior; mitigation advice sound. NOT flagged.

---

## Bugs found

### BUG-1 (Critical) — Hallucinated variable name `v10_lu_transitions` (×2)
- **Class**: 2 (hallucinated variable name) / overlaps 1 (prefix confusion).
- **Trigger** (§1 Critical): "Invented variable name presented as authoritative (no such vm_*/pm_*/v{N}_* exists in declarations.gms)."
- **Doc lines**: GAMS_Functions_Operations.md:434 and :519.
- **Claim**: `v10_lu_transitions(j2,land_from,land_to)` — presented as the variable in cited `q10` equations.
- **Reality**: No `v10_lu_transitions` exists anywhere in develop. The real variable is the interface variable `vm_lu_transitions` (declared `landmatrix_dec18/declarations.gms:23`), used verbatim in the very file cited (equations.gms:21,24,32-33,37-38). Module 10's `landmatrix_dec18` declares ZERO `v10_*` variables — so the `v10_` module-local prefix is itself wrong for this realization.
- **File evidence**: `modules/10_land/landmatrix_dec18/declarations.gms:23` (`vm_lu_transitions(j,land_from,land_to)`); `equations.gms:32-33` uses `vm_lu_transitions`.
- **verify_cmd**: `rg -n 'v10_lu_transitions' /tmp/magpie_develop_ro/` → exit=1, EMPTY (no match). Positive control `rg -ln 'vm_lu_transitions' /tmp/magpie_develop_ro/modules/10_land/` → 4 files (postsolve/declarations/equations/presolve). Positive control `rg -n '\bv10_' .../declarations.gms` → exit=1 (no v10_ vars at all in this realization).
- **confirmed**: true.
- **Fix**: replace both occurrences `v10_lu_transitions` → `vm_lu_transitions`.

### BUG-2 (Major) — Citation drift: `preloop.gms:82` points to materially different content
- **Class**: 10 (stale file:line citation) / 12 (content mismatch).
- **Trigger** (§1 Major): "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different."
- **Doc lines**: GAMS_Functions_Operations.md:291-297.
- **Claim**: `(modules/56_ghg_policy/price_aug22/preloop.gms:82)` for the loop `loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"), s56_fader_start*s56_ghgprice_fader)), ...)`.
- **Reality**: That loop is at `preloop.gms:96`, not 82. Line 82 is `im_pollutant_prices(t_all,i,"n2o_n_indirect",emis_source)$(... > s56_limit_ch4_n2o_price*12/44*265*44/28) = ...;` — a CH4/N2O price cap, unrelated. (Line 85 has `loop(t_all,` with no complex condition.)
- **File evidence**: `modules/56_ghg_policy/price_aug22/preloop.gms:96` (the cited loop verbatim); `:82` is the n2o_n_indirect cap.
- **verify_cmd**: `rg -n 'loop\(t_all' /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/preloop.gms` → `85:loop(t_all,` and `96:loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"),s56_fader_start*s56_ghgprice_fader),`. Read of lines 75-94 confirms :82 = im_pollutant_prices cap.
- **confirmed**: true.
- **Fix**: change citation `preloop.gms:82` → `preloop.gms:96`. (The quoted condition itself is faithful to line 96.)

### BUG-3 (Major) — Fabricated "Official GAMS Documentation" quote; incomplete indexed-operator list
- **Class**: 12 (content-level citation mismatch) / 6 (count drift — lists 4 of 6 operators).
- **Trigger** (§1 Major): "Fabricated count for a set/parameter/realization list" + citation-to-wrong-content. `tier_uncertainty: true` (sand/sor are rarely used; could be argued Minor).
- **Doc line**: GAMS_Functions_Operations.md:462.
- **Claim**: `**Official GAMS Documentation**: "The indexed operators available are: sum, prod, smin, smax" ([UG_Parameters])`.
- **Reality**: That literal sentence is NOT on UG_Parameters.html. The page says: "In addition to the simple operations in Table 1, GAMS also provides the following **six** indexed operations" — `sum, prod, smin, smax, sand, sor`. The doc both misquotes (puts non-existent text in quotation marks) and omits `sand`/`sor`.
- **File evidence**: gams.com/latest/docs/UG_Parameters.html (verified via WebFetch: literal sentence absent; six operations listed: sum/prod/smin/smax/sand/sor).
- **verify_cmd**: WebFetch UG_Parameters.html asking for the literal sentence → "Does the page contain 'The indexed operators available are: sum, prod, smin, smax'? No." + "six indexed operations: sum, prod, smin, smax, sand, sor".
- **confirmed**: true.
- **Fix**: replace line 462 with the actual quote, e.g. `**Official GAMS Documentation**: "GAMS ... provides the following six indexed operations" — sum, prod, smin, smax, sand, sor ([UG_Parameters](...))`. (sand/sor are logical AND/OR over a set; rare but real. At minimum, drop the quotation marks and note four common + two rare.)

---

## Deferred (not editable / not code-refutable)

- **`diag(element1,element2)` semantics** (doc 3.5): `diag` IS a real GAMS function; the UG pages I fetched (UG_OrderedSets, UG_SetDefinition) do not define it, so I could not authoritatively confirm/refute "returns numeric 1/0; differs from sameas (boolean)" against gams.com. To my knowledge the claim is CORRECT (diag returns 1 on the diagonal of a set product). Not flagged; would need the GAMS function-library page for `diag` to verify.
- **`sum` syntax quote** (doc:474): doc quotes `"The index is separated from the reserved word sum by a left parenthesis and from the data term by a comma"`. Actual page text is `"The index over which the summation is done, i, is separated from the reserved word sum by a left parenthesis and from the data term capacity(i,m) by a comma."` The doc's version is a faithful trim (removed the example-specific `i` / `capacity(i,m)`); meaning identical and correct. Borderline-paraphrase-in-quotes; NOT flagged (no behavioral error). Note for maintainers if quote-fidelity is desired.
- **Short-circuit warning** (doc 2.5): correct GAMS behavior, but not stated on the UG_CondExpr page I fetched; deferred as domain-knowledge-correct, not page-verifiable.
- **`m_weightedmean` usage example** (doc:658 `avg_yield = m_weightedmean(yield(i,j), area(i,j), (i,j))`): illustrative, not a code citation; macro signature matches `core/macros.gms:16`. No bug.

---

## Summary

3 confirmed bugs: 1 Critical (hallucinated `v10_lu_transitions` ×2, real name `vm_lu_transitions`), 2 Major (preloop.gms:82→96 citation drift; fabricated "official" indexed-operators quote omitting sand/sor). GAMS function names/semantics, the DNLP restriction, operator tables, the two macro citations, and the equations.gms:14 citation are all correct. Advisory confirmed: function semantics OK, but one official-quote was fabricated.

Note on equations.gms:32 (Section 3.4 vs 4.2): both Section examples cite `:32`. Section 4.2 (sums `land_from`) matches line 32; Section 3.4 quotes a `land_to` sum which is `q10_landreduction` at lines 37-38 — so 3.4's `:32` is a within-file content/line mismatch (should be `:37`). This is folded into BUG-1's fix scope (variable name) but the line-number for the 3.4 instance is independently off; flagged in the schema as part of the per-occurrence fix.
