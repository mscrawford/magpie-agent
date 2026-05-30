# Round 37 adversarial verification — module_80.md

Verifier: adversarial (Opus 4.8 1M). Ground truth: /tmp/magpie_develop_ro (develop worktree).
Date: 2026-05-30.

## Scope note

The three "confirmed bugs" handed off are all citation-drift / conceptual-precision
findings. NONE is a consumer/populator/dependency-set claim (no finding asserts WHICH
modules consume/populate/depend-on an interface variable or parameter). Per method
step 1-2, all three are `class_is_consumer_set = false` -> NOT_CONSUMER_SET, and pass
to the fixer unchanged. I nonetheless re-derived each from develop code; the auditor's
evidence reproduces exactly in all three cases (no refutation, no correction needed).

Note on B3: it concerns whether a *realization* (`lp_nlp_apr17`) declares a *scalar*
(`s80_resolve_option`), surfaced via a cross-realization comparison-table row. That is
a content/conceptual claim (Bug Taxonomy class 4), not a module-level consumer set.
Classified NOT_CONSUMER_SET. I still ran the full both-forms + positive-control grep
protocol on it because it borders on a "does X declare/use Y" set claim.

---

## 80-B1 — NOT_CONSUMER_SET (citation drift; auditor correct)

Doc lines 449 and 957 cite `config/default.cfg:2285` for the "lp_nlp_apr17-only"
comment about `c80_nlp_solver`.

Develop reality (Read /tmp/magpie_develop_ro/config/default.cfg:2278-2293):
- 2285: `cfg$gms$s80_maxiter <- 30  # def = 30`
- 2287: `# Solver settings only for realization \`lp_nlp_apr17\`. All other realizations use \`conopt4\`.`
- 2291: `cfg$gms$c80_nlp_solver <- "conopt4"              # def = conopt4`

The cited line 2285 is `s80_maxiter`, not the comment. The lp_nlp-only comment is at
2287 (2-line drift, same config block). The doc's *substantive* claim — that the switch
applies only to lp_nlp_apr17 — is corroborated verbatim by line 2287. Auditor's fix
(2285 -> 2287, both occurrences) is correct.

rg -n 's80_maxiter|c80_nlp_solver|optimization <-' /tmp/magpie_develop_ro/config/default.cfg:
  2282:cfg$gms$optimization <- "nlp_apr17"              # def = nlp_apr17
  2285:cfg$gms$s80_maxiter <- 30  # def = 30
  2287:# Solver settings only for realization `lp_nlp_apr17`. ...
  2291:cfg$gms$c80_nlp_solver <- "conopt4"              # def = conopt4

Verdict: NOT_CONSUMER_SET (fix is sound; passes through to fixer unchanged).

---

## 80-B2 — NOT_CONSUMER_SET (citation drift; auditor correct)

Doc line 1038 (verification footer): "Verified `nlp_apr17` remains the default in
`config/default.cfg:2280`".

Develop reality:
- 2280: `# *                 See scripts/output/extra/highres.R for details.` (last line of highres comment)
- 2282: `cfg$gms$optimization <- "nlp_apr17"              # def = nlp_apr17`

The default declaration is at 2282, not 2280 (2-line drift). Auditor's fix
(2280 -> 2282) is correct.

Verdict: NOT_CONSUMER_SET.

---

## 80-B3 — NOT_CONSUMER_SET (conceptual table-cell imprecision; auditor correct)

Doc line 471, comparison table, lp_nlp_apr17 cell for `s80_resolve_option` reads
`(LP-relax counter)`. Auditor: lp_nlp_apr17 does NOT declare/use `s80_resolve_option`;
its relax/retry counter is `s80_counter`. Fix: `Not declared (relax counted by s80_counter)`.

Both-forms grep (this scalar has no `(` equation form, so I grepped the bare token,
which catches assignment `s80_resolve_option =` and any `.attr` use):

(1) Absence in lp_nlp_apr17 — confirmed by TWO methods:
  rg -n 's80_resolve_option' /tmp/magpie_develop_ro/modules/80_optimization/lp_nlp_apr17/  -> EXIT 1 (no matches)
  grep -rln 's80_resolve_option' /tmp/.../lp_nlp_apr17/                                     -> EXIT 1 (no matches)
  ls lp_nlp_apr17/  -> declarations.gms input.gms preloop.gms realization.gms solve.gms (search covered all 5 files)

(2) POSITIVE CONTROL in lp_nlp_apr17 (proves the dir is searchable):
  rg -n 's80_counter' /tmp/.../lp_nlp_apr17/  -> EXIT 0:
    solve.gms:9   s80_counter = 0;
    solve.gms:119 s80_counter = s80_counter + 1 ;
    solve.gms:120 until(p80_modelstat(t) = 1 or s80_counter >= s80_maxiter)
    solve.gms:173 if ((s80_counter >= s80_maxiter and p80_modelstat(t) > 2),
    solve.gms:177 display s80_counter;
    solve.gms:179 until (p80_modelstat(t) <= 2 or s80_counter >= s80_maxiter)
    declarations.gms:14 s80_counter      counter (1)
  -> lp_nlp_apr17's relax/retry IS counted by s80_counter, exactly as the proposed fix states.

(3) Where s80_resolve_option actually lives (validates the nlp_apr17 "Declared (4-way cycle)" cell):
  rg -ln 's80_resolve_option' /tmp/.../80_optimization/  ->
    nlp_apr17/solve.gms, nlp_apr17/declarations.gms, nlp_par/solve.gms, nlp_par/declarations.gms
  rg -n 's80_resolve_option' nlp_apr17/solve.gms  -> lines 11,50,52,56,60,64,89
    (s80_resolve_option = 0; ... = +1; if =1 / elseif =2 / =3 / =4; reset $>=4 = 0)
    -> genuine 4-way cycle; the default-column cell is correct and should NOT be touched.

Auditor is right: `s80_resolve_option` is absent from lp_nlp_apr17; the cell `(LP-relax
counter)` can be misread as asserting lp_nlp_apr17 owns an s80_resolve_option (false).
The doc's own prose at line 329 ("LP-warmstart-specific bookkeeping") and line 327
already treat s80_resolve_option as nlp_apr17-side, so the fix removes an internal
inconsistency. Fix `(LP-relax counter)` -> `Not declared (relax counted by s80_counter)`
is accurate.

Verdict: NOT_CONSUMER_SET (conceptual fix is sound).

---

## Bottom line

All three are NOT_CONSUMER_SET. No consumer/populator/dependency-set claim was made or
needed re-derivation against a phantom/omitted member. Auditor evidence reproduced
exactly for all three; fixes are correct and pass to the fixer unchanged. No REFUTE,
no CORRECTED.
