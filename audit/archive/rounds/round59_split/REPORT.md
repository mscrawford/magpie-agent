# R59 — REPORT (split QA round)

**Status**: SKELETON — committed early so a session loss cannot cost the framing.
Numbers marked `<TBD>` are filled at Phase 4 from `collect_scores.py`. Do not quote a `<TBD>`.

**Run**: 2026-07-18, autonomous (Mike away). Branch `r57-rolemap-guard`.
magpie-agent at start `3496a53` · parent MAgPIE `develop @ 0d7ebeb90` (unchanged through the run).

---

## 0. THE LICENSING CAVEAT (PLAN §0.3 — verbatim, not softenable)

**The round mean licenses NOTHING about corpus cleanliness.**

This is not a caveat to soften — it is the round's central epistemic constraint.

R58's 4-question QA arm scored **8.375** on the same corpus where its depth arm found
**46 confirmed defects in 595 claims (7.7%)**. A QA mean over ~12 questions **structurally
cannot** detect a 5–8% claim-level defect rate. Power was raised 5 → 12 for R59; that narrows
the per-arm interval, it does **not** escape this.

What R59 *can* license:
- **Arm A**: whether R58's morning fix commits *broke* something or *left a Critical standing*.
- **Arm B**: first claim-level signal on real hubs that have **never** been depth-audited.

## 0b. ARMS ARE NEVER POOLED (PLAN §0.2)

Arm A re-probes docs that R58's fix agents rewrote hours earlier (~720 insertions, never
validated). **Arm A scores measure "did the fix hold", NOT capability.** Arm B probes
never-depth-audited hubs and measures capability. A pooled mean would be meaningless and would
repeat the 9.52 error. `collect_scores.py` has no code path that pools them.

---

## 1. RESULTS — PER ARM

### Arm A — fix-verification (M11/M29/M59/M70 rewritten regions)

| Probe | Modules | Score | C | M | m | Latent |
|---|---|---|---|---|---|---|
| A1 | 29, 52, 32, 59 | 8.0 | 0 | 0 | 2 | 1 |
| A2 | 29, 30, 10 | 7.0 | 0 | 1 | 1 | 0 |
| A3 | 70, 71, 16, 17 | 8.0 | 0 | 1 | 0 | 1 |
| A4 | 70, 38, 11 | 10.0 | 0 | 0 | 0 | 1 |
| A5 | 11, 59, 52, 56 | 9.0 | 0 | 0 | 1 | 0 |
| **Arm A** | | **raw 8.4** · doc-quality 8.33 (n=3) | **0** | 2 | 4 | **3** |

### Arm B — central + never-depth-audited (M35 #3, M50 #7, M52 #9)

| Probe | Modules | Score | C | M | m | Latent |
|---|---|---|---|---|---|---|
| B1 | 35, 10, 52, 22 | **6.0** | 0 | 1 | 2 | **4** |
| B2 | 35, 52, 28, 32 | 7.0 | 0 | 1 | 1 | 3 |
| B3 | 50, 51, 18, 55 | 7.0 | 0 | 1 | 1 | 2 |
| B4 | 50, 11, 38, 17 | 9.0 | 0 | 0 | 1 | 1 |
| B5 | 52, 56, 59, 29 | 9.0 | 0 | 0 | 1 | 1 |
| **Arm B** | | **raw 7.6** · doc-quality 7.33 (n=3) | **0** | 3 | 6 | **11** |

*(B2 carries a recognition caveat — see F-4.)*

### Regression anchors

| Anchor | Score | Drift | Ground truth re-derived at audit time |
|---|---|---|---|
| G1 (M14 default realization) | 10.0 | **false** | `managementcalib_aug19`, sole realization; exactly 2 equations (`q14_yield_crop:14`, `q14_yield_past:35`); phantom `q14_yieldcalib` still absent (positive control run) |
| G3 (magpie4 version pin) | 10.0 | **false** | v2.70.0 @ `a360d8c9ec1ee7af6c9287791e8b182bf391d355`, `resolution: "sha"`; agrees with `../input/renv.lock`; `lock_file_sha256` canary reproduced byte-identically |

Both anchors stable R49 → R59. **Both auditors independently flagged anchor saturation** — G1 has
two consecutive 10s, G3 six. They are losing discriminating power while the ground truth sits still.
Recommendation (for Mike, not acted on): pair each with a harder probe on the same surface.

---

## 2. HEADLINE

**(a) No Critical stands in R58's rewritten text. Arm A: 0 Criticals in 5 probes across all four
fix commits.** The §9 escalation trigger did not fire. R58's fixes held. That is *all* Arm A
licenses — not capability, not cleanliness.

**(b) The interesting result is where the arms differ, and it is not the score.**

| | raw mean | doc_quality_mean | Critical | Major | Minor | **latent doc bugs** |
|---|---|---|---|---|---|---|
| Arm A (rewritten hours earlier) | 8.4 | 8.33 | 0 | 2 | 4 | **3** |
| Arm B (never depth-audited) | 7.6 | 7.33 | 0 | 3 | 6 | **11** |

The **answer** scores are close (8.4 vs 7.6, n=5 each — well inside noise at this power). The
**latent doc-bug** count is 3 vs 11. Latent bugs are exactly the case where the answerer got it
right *anyway* — so they are invisible to the score and visible only because rubric §1.5 forces
the auditor to check the doc the answer leaned on.

That is the score-the-answer-not-the-doc blind spot, demonstrated at round scale: **a QA mean would
have rated these two arms as roughly equivalent. The doc layer underneath them is not.**

Both Criticals in the whole round are **latent**:
- `module_70_notes.md` falsely asserts "M70 reads" `vm_costs_additional_mon` (A4-L1) — in the very
  entry that exists to prevent M70/M71 misattribution.
- `module_52.md` never received R58's `stockType` correction (B5-L1) — so `actualNoAcEst`, the slice
  Module 56 prices **by default**, is invisible in the carbon module's own doc. G2 pattern verbatim.

**(c) CONFOUND — read (b) with this attached.** Arm B's auditors received *more targeted
"adjudicate this specific doc claim" hints* than Arm A's (B1 got four; B3 and B4 were each asked to
adjudicate a named doc contradiction). An auditor told to adjudicate a contradiction finds more
latent bugs than one not told. **An unknown share of the 3-vs-11 gap is method, not corpus** — the
same confound R58 flagged between R55's imposed taxonomy and its own open-ended lens, and I
reproduced a version of it here. n=5/arm, no randomisation, different modules, no power to
separate. Treat 3-vs-11 as a **lead worth a properly matched round**, not an established rate.

**(d) Arm B did what it was for.** M35 — the **#3 hub, never claim-level audited** — produced the
round's lowest score (B1, 6/10) and its densest doc gap: `module_35.md` §8 compresses
`presolve.gms:140-234` into three unsourced bullets, so a docs-only reader **cannot** recover the
per-pool Module 22 restrictions (`:162`, `:201`, `:231`). That gap would reproduce in every future
natveg answer. This is the survivorship mechanism PLAN §6 predicted: M35 is absent from AGENT.md's
hub list, so rounds following question-design rule #4 kept steering away from it.

---

## 3. FINDINGS FOR MIKE (raised during execution; none acted on beyond scope)

Full detail in `STATUS.md`. Summary:

- **F-1** — `probe_dedup_ledger.json` stale by ~6 rounds (last appended source round R52; R53–R58
  never appended). Step 5c silently skipped again — the failure the 2026-05-29 note calls "FIXED".
  Also: PLAN §3's dedup framing is off (module_70 is 48 not 51; and ≤51 at R59 means *eligible*,
  not off-limits). Round unaffected — §3's binding consequence rests on R58 having rewritten those
  docs, not on the ledger.
- **F-2** — AGENT.md's hub list is probably wrong (PLAN §6). **Flagged only**, per §0.4.
- **F-3** — **§6b's M11 delta RESOLVED: R58 was right.** The role-map extractor counts
  `NAME.scale(...) =` as population, inflating `populated_by`. `vm_cost_transp` is declared *and*
  populated by M40; M11 only reads it. Degree 33 unaffected → Arm B selection stands. M70's
  19-vs-16 delta remains OPEN (read-side, different mechanism). **Independently corroborated**: B4's
  auditor hit the same trap live at `50_nr_soil_budget/.../scaling.gms:8`. The extractor also feeds
  `check_attribution_omissions.py`, and producer/consumer sets are the R20 Critical anchor class.
- **F-4** — partial blinding leak on B2 (its answerer recovered macro bodies from *archived* round
  answers). Score carries a recognition caveat; not a re-run trigger.
- **F-5** — new phantom class with **zero gate coverage**: prose module-number attribution.
  `module_29.md:193` invents a "Module 33" (there is no Module 33; `q33_marginal` is a
  33rd-percentile suitability label in set `marginal_land29`). Gates pass green because the
  identifier is backticked and genuinely exists — only the prose attribution is false.
  A2's auditor swept the corpus with a positive control: exactly one hit.
- **F-6** — MAgPIE **source-prose ambiguity** that will keep regenerating doc bugs:
  `50_nr_soil_budget/.../equations.gms:20` says inorganic fertilizer "are a free variable", but
  `declarations.gms:9-10` declares it under `positive variables`. Any doc written from the `*'`
  comments inherits the error (it already reached `cross_module/nitrogen_food_balance.md:104`).
  Recommend inoculating the doc, not just patching the line.

## 4. METHOD NOTES

- **Answerers blinded** from `round59_split/` and `validation_rounds.json` — no probe could see
  which regions R58 rewrote or which arm it was in (leak on B2 only, see F-4).
- **Auditors blinded to arm membership** — severity judgments not biased by knowing a doc was
  rewritten hours earlier. Does not change what Arm A scores MEAN (§3).
- **G3 auditor read `project/version_pins.json` directly at audit time** as the rubric requires;
  no hardcoded version was scored against.

## 5. WHAT WAS NOT DONE (deliberate)

- **Nothing pushed.** Stopping after Step 5c per §9; push needs Mike (§0.1).
- **AGENT.md hub list untouched** (§0.4).
- **The 3 held findings untouched** — `module_56.md:1138/:1150`, `module_17.md:899`,
  `Module_Dependencies.md` dependent counts. No truth number written (§0.6).
- Ledger backfill for R53–R58: out of scope.
- Role-map `.scale` extractor bug: diagnosed, **not fixed** (out of scope).
