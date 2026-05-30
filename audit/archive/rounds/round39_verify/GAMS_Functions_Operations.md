# Round 39 Adversarial Verification — GAMS_Functions_Operations.md

Verifier: Opus 4.8 (1M ctx), adversarial. Ground truth: official GAMS docs (gams.com) for
language claims; `/tmp/magpie_develop_ro` for MAgPIE-convention claims.

Repo confirmed: `/tmp/magpie_develop_ro` (MAgPIE develop, read-only).
Default realization for module 10 = `landmatrix_dec18` (only realization present; `ls -d
modules/10_land/*/` → input/ + landmatrix_dec18/).
Default realization for module 56 = `price_aug22` (config/default.cfg:1611 `cfg$gms$ghg_policy
<- "price_aug22"`; only price_aug22 + input present).

grep discipline note: `grep -r` / `rg` exit 1 on no-match, which the harness surfaces as an
error and (in a parallel batch) cancels siblings. I re-ran every absence probe standalone and
appended a positive control. Both methods (rg + grep -r) agreed on the v10_ absence.

---

## GFO-1 — Hallucinated variable name `v10_lu_transitions` (doc:434, :519)  [Critical]

Class: producer_declaration (the corrected name's declaration is the safety pivot).

### STEP A — Mechanical citation check
- `test -f modules/10_land/landmatrix_dec18/declarations.gms` → EXISTS; `wc -l` = 52.
  Line 23 = `vm_lu_transitions(j,land_from,land_to) Land transitions between time steps (mio. ha)`.
  → contains the claimed `vm_lu_transitions` token. PASS.
- `test -f .../equations.gms` → EXISTS; `wc -l` = 54.
  - :32 = `        sum(land_from$(not sameas(land_from,land_to)),`
  - :33 = `        vm_lu_transitions(j2,land_from,land_to));`
  - :37 = `        sum(land_to$(not sameas(land_from,land_to)),`
  - :38 = `        vm_lu_transitions(j2,land_from,land_to));`
  All four lines exist and use `vm_lu_transitions` verbatim. PASS.
- Doc lines 434 and 519 (read from target doc) BOTH literally contain `v10_lu_transitions`.
  Confirmed the bug exists in the doc as claimed.

citation_ok = TRUE.

### STEP B/C — Adjudication
Existence of `v10_lu_transitions` anywhere in develop:
- Method 1 `rg -n 'v10_lu_transitions' /tmp/magpie_develop_ro/` → exit 1, NO MATCHES.
- Method 2 `grep -rn 'v10_lu_transitions' /tmp/magpie_develop_ro/modules/` → exit 1, NO MATCHES.
- Positive control `rg -n 'vm_lu_transitions' modules/10_land/` → 14 hits (declarations:23,
  equations:20/24/33/38, presolve:13/16/17/20/21, postsolve:17/30/43/56). Search works in-dir.
- `rg 'v10_' .../declarations.gms` not needed beyond inspection: declarations.gms declares
  vm_landexpansion, vm_landreduction, vm_cost_land_transition, vm_lu_transitions — ZERO v10_*
  module-local variables. Auditor's "the v10_ prefix is itself wrong" claim is correct.

The real variable is the interface variable `vm_lu_transitions`, declared at
landmatrix_dec18/declarations.gms:23 and used verbatim in the cited equation lines.

VERDICT: UPHELD. Fix is safe — replace `v10_lu_transitions` → `vm_lu_transitions` at doc
lines 434 and 519.

---

## GFO-2 — Stale citation `preloop.gms:82` should be `:96`  [Major]

Class: other (file:line citation drift; content faithfulness already validated mechanically).

### STEP A — Mechanical citation check
- `test -f modules/56_ghg_policy/price_aug22/preloop.gms` → EXISTS; `wc -l` = 123 (both 82 and
  96 in range).
- Line 82 = `im_pollutant_prices(t_all,i,"n2o_n_indirect",emis_source)$(im_pollutant_prices(...
  > s56_limit_ch4_n2o_price*12/44*265*44/28) = s56_limit_ch4_n2o_price*12/44*265*44/28;`
  → an n2o_n_indirect / CH4-N2O price cap, NOT the quoted loop. Confirms auditor.
- Line 96 = `loop(t_all$(m_year(t_all) > max(m_year("%c56_mute_ghgprices_until%"),
  s56_fader_start*s56_ghgprice_fader)),` → verbatim match to the doc's quoted snippet
  (doc:293-294). The proposed-fix citation `preloop.gms:96` contains the claimed loop. PASS.
- Realization is the default (price_aug22), so the active code path is what's cited. Good.

citation_ok = TRUE. The current doc citation (:82) points at materially different content; the
quoted condition is faithful to :96.

VERDICT: NOT_REVIEWABLE class=other → pass to fixer unchanged. Fix is safe and confirmed:
change doc:291 citation `:82` → `:96`.

---

## GFO-3 — Fabricated "Official GAMS Documentation" quote + omitted operators (doc:462)  [Major]

Class: other (GAMS-language quote/operator-list; verified against gams.com, not module code).

### STEP A — Mechanical citation check (ground-truth page)
WebFetch https://www.gams.com/latest/docs/UG_Parameters.html:
- The literal sentence "The indexed operators available are: sum, prod, smin, smax" is NOT on
  the page. The page introduces them as: "In addition to the simple operations in Table 1,
  GAMS also provides the following six indexed operations." (six, not four).
- Enumerated set (Table 2): sum, prod, smin, smax, sand, sor — exactly six. The doc omits
  `sand` (conjunction) and `sor` (disjunction).
- Cross-check on the adjacent quote at doc:474 ("The index is separated from the reserved word
  sum by a left parenthesis and from the data term by a comma"): the page DOES contain an
  almost-verbatim form ("The index over which the summation is done, `i`, is separated from the
  reserved word `sum` by a left parenthesis and from the data term `capacity(i,m)` by a
  comma."). doc:474 is a faithful paraphrase — NOT fabricated; fixer should leave :474 alone.

citation_ok = TRUE (the cited page exists and is the right page; the misquote is the bug).
The auditor's evidence reproduces exactly: the quoted sentence is absent, six operators exist,
two are omitted.

VERDICT: NOT_REVIEWABLE class=other → pass to fixer. Fix is safe. Recommend the auditor's
replacement; the quotation marks must go (the string is not a real quote) and sand/sor should
be named. tier note: sand/sor are rarely used in MAgPIE, but the fabricated quote alone
justifies Major (a doc presenting an invented sentence as an official quote is the core defect).

---

## GFO-4 — Citation `equations.gms:32` points at the wrong equation (land_from vs land_to) (doc:431)  [Major]

Class: realization_structure (which equation the landmatrix_dec18 realization defines at which
line: q10_landexpansion vs q10_landreduction).

### STEP A — Mechanical citation check
equations.gms (landmatrix_dec18) equation block, read with line numbers:
- :30 `q10_landexpansion(j2,land_to) ..`
- :31 `vm_landexpansion(j2,land_to) =e=`
- :32 `sum(land_from$(not sameas(land_from,land_to)),`   ← sums over land_FROM
- :33 `vm_lu_transitions(j2,land_from,land_to));`
- :35 `q10_landreduction(j2,land_from) ..`
- :36 `vm_landreduction(j2,land_from) =e=`
- :37 `sum(land_to$(not sameas(land_from,land_to)),`     ← sums over land_TO
- :38 `vm_lu_transitions(j2,land_from,land_to));`

Proposed-fix citation `equations.gms:37` exists (file 54 lines) and is the `sum(land_to$...)`
line. PASS.

### STEP B/C — Adjudication (realization_structure, against THIS realization only)
The doc snippet at doc:433-434 quotes `sum(land_to$(not sameas(land_from,land_to)),
v10_lu_transitions(...))` — i.e. the land_TO form. In landmatrix_dec18 the land_to sum is the
body of q10_landreduction at lines 37-38, NOT line 32 (which is q10_landexpansion's land_from
sum). So the :32 citation is bound to a different equation than the quoted content. Auditor
correct.

Auditor's parenthetical also checked: the Section-4.2 instance at doc:516-519 quotes the
land_FROM form and cites :32 — line 32 IS the land_from sum, so that instance is internally
consistent and must NOT be changed. Confirmed.

VERDICT: UPHELD. Apply BOTH at doc:431: (a) change citation `:32` → `:37`; (b) GFO-1 name fix
(`v10_lu_transitions` → `vm_lu_transitions`) on doc:434. Citing :37 (the `sum(` line) is correct
convention even though the variable token is on :38.

---

## Summary

| Bug | Class | citation_ok | Verdict |
|-----|-------|-------------|---------|
| GFO-1 | producer_declaration | true | UPHELD |
| GFO-2 | other | true | NOT_REVIEWABLE (pass-through; fix confirmed) |
| GFO-3 | other | true | NOT_REVIEWABLE (pass-through; fix confirmed) |
| GFO-4 | realization_structure | true | UPHELD |

All four reproduce mechanically. No CITATION_FAILED, no REFUTED. Extra guidance for fixer:
doc:474 and doc:516-519 are CORRECT and must be left untouched (only doc:462, :291, :431/434,
:519 change).
