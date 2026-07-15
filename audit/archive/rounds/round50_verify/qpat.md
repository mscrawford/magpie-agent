# Round 50 Adversarial Verification — Query_Patterns_Reference.md

Target doc: `<magpie-agent>/core_docs/Query_Patterns_Reference.md`
Ground truth: `/tmp/magpie_develop_ro` (develop worktree, read-only)
Verifier: adversarial, mechanical-first.

---

## qpat-B1 — VERDICT: CORRECTED

**Class:** other (formula/value/prose; but see semantic note — this is really a mislabeling, not a numeric drift)

**Claim in doc (Query_Patterns_Reference.md:155):** `- 5 years: 44% of gap closed`

**Auditor's reality claim:** With `i59_lossrate = 1 - 0.85^t`, gap-closed at 5yr = `1 - 0.85^5 = 0.556 = 56%`, not 44%. 44% = `0.85^5` = gap REMAINING. The 10yr (80%) and 20yr (96%) entries are correct gap-closed; only 5yr was (per auditor) computed as gap-remaining, making the table internally inconsistent with its own formula. Proposed fix: 44 -> 56.

### STEP A — MECHANICAL CITATION CHECK — citation_ok = TRUE

```
$ test -f /tmp/magpie_develop_ro/modules/59_som/cellpool_jan23/preloop.gms
EXISTS
$ wc -l /tmp/magpie_develop_ro/modules/59_som/cellpool_jan23/preloop.gms
116            # line 45 in range
$ rg -n 'i59_lossrate' .../preloop.gms
45:i59_lossrate(t)=1-0.85**m_yeardiff(t);
```
file_evidence line 45 contains the exact identifier `i59_lossrate` and the formula `1-0.85**m_yeardiff(t)`. Citation valid.

Doc target line confirmed:
```
Query_Patterns_Reference.md:155 = "- 5 years: 44% of gap closed"   (read directly)
```

### STEP B — CLASSIFY
`other` — a numeric/prose value, not a consumer/producer/realization-structure set. Per protocol `other` is normally NOT_REVIEWABLE once citation passes. BUT the auditor's *reasoning* (internal-inconsistency diagnosis + the specific fix direction) is mechanically checkable against the source, and it does NOT reproduce. So I adjudicate rather than rubber-stamp.

### STEP C — ADJUDICATION

**(1) Auditor arithmetic — CORRECT.**
```
$ python3: for t in 5,10,20: closed=1-0.85**t ; remaining=0.85**t
5yr:  closed=55.6%  remaining=44.4%
10yr: closed=80.3%  remaining=19.7%
20yr: closed=96.1%  remaining= 3.9%
```
So 44% IS the gap-remaining fraction at 5yr; 55.6% is gap-closed. The auditor's algebra checks out.

**(2) Auditor DIAGNOSIS — REFUTED.** The auditor says the doc author miscomputed the 5yr cell (as gap-remaining) while correctly computing 10yr/20yr (as gap-closed). False. The doc transcribed all three numbers verbatim from the MAgPIE source comment:
```
$ rg -n '44%|80%|96%' .../preloop.gms
42:*' of a lossrate of 15% per year resulting in 44% in 5 years, 80% in 10 years
43:*' and 96% in 20 years. The lossrate for a given timestep is than calculate by
```
The code author's own comment writes "44% in 5 years, 80% in 10 years and 96% in 20 years." The doc's 44/80/96 are a faithful copy of this comment, NOT three independent computations one of which slipped. The "internal inconsistency" the auditor attributes to the doc actually originates IN THE SOURCE COMMENT: `i59_lossrate = 1 - 0.85^t` is the loss fraction, whose values are 55.6 / 80.3 / 96.1; the comment's 80 and 96 match `1-0.85^t` (rounded) but its 44 matches `0.85^t` (the complement). The source comment is itself loose/mixed; the doc inherited that.

**(3) Auditor FIX DIRECTION — REJECTED.** Changing 44 -> 56 would make the doc DIVERGE from the source-code comment it is quoting, substituting the doc author's arithmetic for the MAgPIE author's stated characterization. Under the project's CODE-TRUTH primary directive ("describe ONLY what is actually implemented / stated in the code"), silently overwriting a faithful transcription with a recomputed value is the wrong move. It also leaves the *real* defect — the mislabel — unaddressed: 44% is presented under the header "Convergence Dynamics (movement toward new state)" and the label "of gap closed," but 44% is gap-REMAINING.

```
Query_Patterns_Reference.md:150  **3. Convergence Dynamics** (movement toward new state):
                              152  Convergence: 15% annual movement toward equilibrium
                              153  Formula: i59_lossrate(t) = 1 - 0.85^timestep_length
                              155  - 5 years: 44% of gap closed     <- 44% is gap REMAINING, mislabeled
                              156  - 10 years: 80% of gap closed    <- matches 1-0.85^10 = 80.3% (OK as gap-closed)
                              157  - 20 years: 96% of gap closed    <- matches 1-0.85^20 = 96.1% (OK as gap-closed)
```

### Corrected claim to apply

Do NOT change 44 -> 56. Instead correct the LABEL/semantics so the doc is both faithful to the source comment AND internally coherent. Recommended replacement for line 155 (and a one-line clarifier):

`- 5 years: 44% of carbon lost (i.e. 0.85^5 = 0.444 remaining; equivalently ~56% of the gap closed)`

Rationale: keeps the 44% that the MAgPIE source comment (preloop.gms:42) actually states, while flagging that 44% is the loss/remaining figure, not "gap closed." 10yr/20yr lines are fine as-is under "gap closed" (they match 1-0.85^t). If the fixer prefers a single consistent metric across all three rows, the alternative is to relabel the block as "fraction lost / remaining" and use 44 / 80 / 96 as gap-CLOSED only for 10 & 20 — but the cleanest minimal edit is the per-line clarifier on 155 above, because 80 and 96 already read correctly as gap-closed.

**This is NOT a clean numeric swap; the auditor's proposed 56 would introduce a code-vs-doc divergence. Hence CORRECTED, not UPHELD.**

---

### Summary
- Citation: VALID (file exists, line 45 in range, contains `i59_lossrate` + formula).
- Auditor arithmetic: correct.
- Auditor diagnosis ("doc miscomputed one cell, internally inconsistent"): REFUTED — doc transcribes the source comment 44/80/96 verbatim (preloop.gms:42-43); the looseness is in the SOURCE.
- Auditor fix (44->56): REJECTED — would diverge from the code comment.
- Action: CORRECTED — fix the mislabel ("gap closed" vs gap-remaining for the 44% row), preserving the source-stated 44%.

---

### Verifier-2 concurrence (independent re-derivation)

Independently re-ran Step A + the arithmetic and confirm verifier-1's findings:
- preloop.gms exists (116 lines), :45 = `i59_lossrate(t)=1-0.85**m_yeardiff(t);`; doc :155 = `- 5 years: 44% of gap closed`.
- `1-0.85^t` = 55.6/80.3/96.1 for t=5/10/20; `0.85^t` = 44.4/19.7/3.9. Comment's 80/96 match the lossrate `1-0.85^t`; its 44 matches the complement `0.85^t`. The 5yr cell is the lone outlier in BOTH the code comment AND the doc — the doc faithfully copied the source comment (preloop.gms:42-43).

CONCUR with verdict **CORRECTED** and with rejecting the naive 44->56 swap (it would substitute recomputed arithmetic for the source-stated value, violating CODE-TRUTH and leaving the actual label defect unfixed).

One refinement to the rationale (does not change the verdict or the fix): verifier-1 states flatly "44% is gap REMAINING, mislabeled as gap closed." Mathematically 44.4% = `0.85^5` = remaining, so that reading is reasonable — BUT the code author's intent is ambiguous: line 42 attributes 44% to "a lossrate of 15% per year," i.e. the author believed 44% was the LOSS/closed figure. So the source defect is better described as "an internally inconsistent comment — the author intended a loss/closed figure but wrote the complement of the formula's output (44 instead of 55.6)," rather than cleanly "a remaining value with a closed label." Either framing yields the same minimal fix: a per-line clarifier on :155 that preserves the source-stated 44% while disambiguating loss/remaining vs gap-closed (verifier-1's recommended replacement stands).
