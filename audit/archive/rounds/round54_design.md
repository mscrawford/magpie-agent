# R54 — Post-sync verification round (design)

**Status:** PREPPED, not run. **Date prepped:** 2026-07-14. **Code base:** develop `0d7ebeb90`.
**Trigger:** the 2026-07-14 sync + PR-integration session rewrote 13 docs. R53 (a 2-probe drift-triggered round on that same content) found **1 Critical + 1 Major self-inflicted defect**, both of which passed the 42-check syntactic validator with 0 errors. That is a demonstrated defect rate in freshly-written content, so the rest of it must be assumed guilty until audited.

---

## Why this round is not routine

R53's Critical was a **false bug report** written into the shared docs, accusing a colleague's just-merged PRISMA feature of being silently broken. Every premise was true; the conclusion was false. The agent verified the GAMS (consuming) layer exhaustively and **never grepped the R (producing) layer** — `npi_ndc_aff_pol.cs3` is gitignored and regenerated at run start by `scripts/start_functions.R:380-391`, whose guards were added *by the very commits being accused*.

**That failure class is not covered by anything in the existing engine.** `GREP_GUARD` covers substring false-positives, the `.attribute` form, and errexit truncation. It does not cover *"you are reasoning about an artifact whose producer you never located."* R54 must inject that rule explicitly, or it will reproduce the same error while feeling rigorous.

---

## Stage 0 — Prerequisite (must run first)

The engine verifies against a detached read-only develop worktree that does **not currently exist**:

```bash
git -C /Users/turnip/Documents/Work/Workspace/magpie worktree add --detach /tmp/magpie_develop_ro refs/magpie-canonical-develop
git -C /tmp/magpie_develop_ro rev-parse --short HEAD    # must print 0d7ebeb9
```

---

## Stage 1 — Doc-validator A: mechanical (free, ~2 min)

```bash
bash scripts/validate_consistency.sh
```
Expected baseline: **42 checks, 41 pass, 0 errors, 1 known-benign warning** (6 files legitimately reference `CLAUDE.md` — that IS the deployed copy's filename). Anything else is new drift.

This layer checks **form** (does the symbol exist, does the line number resolve). It provably **cannot** check inference: both R53 defects passed it cleanly. It is a necessary gate, not evidence of correctness.

---

## Stage 2 — Doc-validator B: semantic, doc-vs-code (`doccentric` + `verify`)

Engine: `audit/tools/doc_audit_round.workflow.js` — Opus full-doc audit per doc, adversarial verifier refute-pass, gated Sonnet fixes, syntactic gate.

```
mode: 'doccentric'   verify: true   round: 54
```

### Tier 1 — the 10 docs this session changed (MUST audit)

These carry the agent's own **un-refuted reasoning**, which is precisely what nothing else inspects.

| Doc | klass | Why high-risk |
|---|---|---|
| `modules/module_35.md` | module | Rewrote §6.6 (`q35_prod_other`), the carbon narrative, and the `_uncalib` consumer list. **Carries Lead B.** |
| `modules/module_14.md` | module | New interface `im_growing_stock_ysf`: 5th formula block, clamps, glossary, consumer entries |
| `modules/module_32.md` | module | Rewritten twice — once wrong (the retracted silent-zero), once corrected. **Highest churn in the session.** |
| `modules/module_32_notes.md` | module | **Brand new file, written twice.** Its first version was the Critical. Assume nothing. |
| `modules/module_22.md` | module | LandMark enumerations + the ICCA limitation rewrite (validator-invisible class) |
| `cross_module/carbon_balance_conservation.md` | cross_module | The "one growth curve" invariant + both caveats. **Carries Lead A.** |
| `reference/GAMS_MAgPIE_Patterns.md` | reference | 15 symbols replaced; naming tables rebuilt from real code; allowlist deleted |
| `reference/AGENT_QUERY_FLOWCHART.md` | reference | `vm_carbon_price` → the real M56 chain |
| `reference/GAMS_Advanced_Features.md` | reference | Allowlist marker added (`vm_production`, `vm_trade`) |
| `agent/helpers/debugging_gams_errors.md` | helper | **Benni's PR #6, merged — never independently audited against code.** Its GAMS error-code table (141/149/170/171/257/455) and the `EXECERROR`-skipped-solve mechanism are unverified by us. |

### Tier 2 — corpus breadth ("a little more verification on the total corpus")

Rotate in the **least-recently-audited** module docs (query `validation_rounds.json` + the per-module `Last Verified` footers). Suggested: 6-8 docs not touched since R45-R47. This is the only part of the round that is *discretionary* — cut it first if budget is tight.

### The two directed leads (attach as `probe_question`, with a hard decidability split)

Both came from an adversarial auditor on 2026-07-14. **Neither is established.** They are recorded in `audit/BACKLOG.md` and deliberately NOT asserted in the module docs.

**Lead A — is the youngsecdf yield/carbon mismatch ALSO live for `secdforest` proper?**
> `q35_prod_secdforest` (`pot_forest_may24/equations.gms:144-147`) reads the purely **FRA-calibrated** `im_growing_stock(...,"secdforest")`. `q35_carbon_secdforest` (`:49-51`) reads `p35_carbon_density_secdforest` — a **blend** of calibrated + uncalibrated weighted by the natural-origin share (`presolve.gms:248-252`). Natural-origin area is bound against harvest (`:177-180`), which mitigates but may not close the gap, since the blend is an age-class average.

**Lead B — is `module_35.md:305`'s rationale for the natural-origin feature backwards?**
> It says the FRA calibration produces a *suppressed* growth rate, so applying it would *underestimate* youngsecdf carbon accumulation. The audit's numerical replication of the M52 bisection (`normal_dec17/preloop.gms:23-73`) claims the calibration **raises** `k` in 10 of 12 regions (and lowers it in SSA/OAS) — which would make the stated rationale inverted for most of the world.

**MANDATORY framing for both — do not skip this, it is the whole lesson of R53:**

1. **Split the question by decidability, and answer only the decidable half.**
   - *Decidable by reading code:* which curve feeds which equation (structural). Settle this.
   - *NOT decidable by reading:* whether the residual gap is **material**, and whether some layer you have not read closes it. **Do not return a verdict on this half.** Return the exact experiment that would settle it.
2. **Enumerate the layers you did NOT check, by name.** For Lead A specifically: the `pcm_carbon_stock` carry-forward (`postsolve`), the M56 pricing scope (`f56_emis_policy.csv`), and the magpie4 reporting layer. The R53 auditor explicitly said it had *not* traced the carry-forward.
3. **Try to REFUTE.** Default to "no defect". A confirmed-real verdict requires reproducible mechanical evidence, not a compelling derivation.
4. Lead B is a **numerical** claim. Either replicate the bisection and show the numbers, or say you did not and mark it unresolved. **Do not adjudicate it by reading prose.**

---

## Stage 3 — QA: answer-quality flywheel (`hybrid`)

Only after Stage 2's fixes land. Tests whether the **corrected** docs now produce correct answers.

Probes must include:
- **The retraction regression** — *"Can I run `c32_aff_policy = ndcdelay`?"* A docs-only answerer must now say **yes, it works** (regenerated at run start), and must surface the narrow `cfg$recalc_npi_ndc <- FALSE` footgun. If it still says "silently broken", the retraction did not take.
- **The youngsecdf coupling** — must name `im_growing_stock_ysf`, must NOT claim a universal direction for the pre-fix bias.
- **Regression anchors G1-G4** (rotate; `audit/flywheel_rubric.md` §6) — G3/G4 protect the magpie4 version-pin discipline.
- **The offline principle** — *"How do I find out what `reportEmissions()` does?"* The answer must read the pinned `.cache/sources/magpie4/` clone, NOT propose fetching a URL.

**Score the DOC, not the answer** (`doc_error_answerer_beat_it`). In R53 the answerers were flawless and still wrong, because the doc was wrong. A high answer score over a bad doc is the failure mode this rubric line exists to catch.

---

## Positive control (non-negotiable)

**Plant a known doc bug and confirm the round goes RED on it.** A clean R54 is otherwise ambiguous between *"the corpus is clean"* and *"the auditors are blind"* — and I have just demonstrated that a fluent, well-evidenced audit can be confidently wrong.

Cheapest control: on a scratch copy of a Tier-1 doc, flip one interface attribution (e.g. re-point `im_growing_stock_ysf`'s producer from M14 to M52) and verify the doc-auditor flags it as a MANDATE-18 role-attribution bug. Discard the scratch copy after. (Convention: `synthesize-known-bug-test-for-new-validator`.)

---

## New rule to inject into every auditor prompt (the R53 lesson)

> **Before claiming any input, parameter, or data column is missing, stale, unpopulated, or silently zero — find out WHO PRODUCES IT.** A file under `modules/*/input/` is **not** necessarily an input you were given: `*.cs*` is gitignored and several inputs are **run-time products of `scripts/`**. Reading the file's current bytes and its git history tells you what it IS, not what it WILL BE when the model actually runs. Grep the **whole repo root** for the switch name and the filename — `grep -rn "<switch>" .` — including `scripts/`, `config/`, and the R layer. Then read the accused commit's **non-`.gms`** files. This exact failure produced R53's Critical: a false bug report against a colleague's merged feature, where the guards refuting it had been added by the very commits being accused.

---

## Cost / scope tiers

| Tier | Content | Rough agent count |
|---|---|---|
| **Minimum** | Stage 1 + Stage 2 Tier-1 only (10 docs, `doccentric`+`verify`) + the 2 leads | ~25-30 |
| **Recommended** | Minimum + Stage 3 QA (6-8 probes + anchors) | ~40-45 |
| **Full** | Recommended + Stage 2 Tier-2 corpus rotation (6-8 more docs) | ~60-70 |

Weekly rate-limit was ~70% consumed at prep time (resets in ~4 days). **Full** is affordable only after the reset, or accepting the burn.
