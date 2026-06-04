# Round 44 — Diagnostic flywheel on the weak spots (+ lens-bridge instrumentation)

**Status**: DESIGNED, not yet run. Follow `agent/commands/validate-semantic.md` to execute.
**Type**: `targeted` (diagnostic re-test), schema as in `audit/validation_rounds.json` metadata.
**Designed**: 2026-06-04
**Designed-from**: coverage analysis in `audit/tools/viz_validation_coverage.py` (figs 5–7 current-quality lens).

---

## 1. Why this round exists

The current-quality visualizations (latest-score-per-module) isolated the weak spots that the
all-rounds mean had smeared out. Two distinct buckets, with corrected priorities after reading the
actual probe history (not just the scores):

| Module | Last test | Last score | Real status | Priority |
|--------|-----------|-----------|-------------|----------|
| **M20 processing** | R27 | **4.0** | genuinely weak on the core "primary→secondary conversion" question; predates the R30–R32 doc push (111 bugs fixed) so the 4.0 is **unverified against current docs** | **HIGH** |
| **M09 drivers / M15 food / M17 production** | R41 | 6.0 | the 6.0 is **one shared question** — a socioeconomic driver→demand→production chain trace. The weak *area* is that chain, not three independent modules. | **HIGH** |
| M54 phosphorus | R28 | 9 | healthy when last tested; only *stale* (pre-doc-push). Drift-check, not a fix target. | LOW |
| M71 lvst disagg | R22 | 8 | healthy when last tested; only *stale*. Drift-check. | LOW |

**Diagnostic intent**: this round is not just "score these modules again." It is built to answer
*why* the weak area is weak, so we know whether to stop at a doc fix or escalate to a lens audit.
Every bug is classified on TWO axes (see §4): the standard root-cause taxonomy **plus** a
`verifier_gap` tag identifying which anti-confabulation MANDATE (1–20, `agent/helpers/verifiers.md`)
*should* have prevented it. A MANDATE that recurs as the gap across unrelated probes is the
signature of a machinery problem — that is the escalation trigger to a focused lens audit (§5).

---

## 2. Probe set (5 new + 1 rotating regression anchor)

Each GAMS probe spans ≥3 modules and requires ≥2 doc files (per validate-semantic.md design rules).
Each carries an explicit **lens check** the auditor must score separately from surface correctness.

### P1 — Population → food demand → production (drivers chain, mechanism axis)
> *In MAgPIE's **default** configuration, when a higher-population SSP raises food demand, trace the
> mechanism by which that demand signal reaches realized crop production. Name the modules and the
> specific interface variable passing the signal at each hop (drivers → food demand → demand
> aggregation → production). For **each hop**, state explicitly whether the relationship is a solved
> GAMS equation or a parameterized input passed between modules.*

- Modules: 09, 15, 16, 17 · Docs: `module_09.md`, `module_15.md`, `module_16.md`, `module_17.md`
- **Lens check (parameterization-vs-mechanism)**: the answer MUST classify each hop as equation vs
  parameter. This is the exact distinction CLAUDE.md flags as the #1 confabulation risk.
- Archetype: cross-module causal chain (the systematically weakest archetype, mean 6.5).
- Fresh-angle note: R41 asked a generic "trace socioeconomic drivers" question; this forces the
  per-hop mechanism call, a capability not exercised by recognition of the R41 framing.

### P2 — Processing primary→secondary conversion (the M20 4.0 re-test)
> *In the **default** config, explain how module 20 (processing) converts primary agricultural
> products into secondary products (e.g., oils, sugar, ethanol). Name the conversion equation and
> the parameter holding conversion factors. Does processing **create or consume** the secondary
> products that module 16 balances against demand? Identify which modules supply the inputs and
> which consume the outputs.*

- Modules: 20, 16, 17/62 · Docs: `module_20.md`, `module_16.md`, `module_20_notes.md` (if present)
- **Lens check (active realization)**: answer must state M20's active realization (verify via
  `grep cfg$gms$processing ../config/default.cfg`) before describing equations.
- **Lens check (parameterization)**: conversion factors are parameterized — answer must not present
  them as an endogenous/optimized outcome.
- Purpose: re-establish current state vs the R27 4.0. If still weak → doc fix; classify the bug
  source carefully (was the R27 failure doc_error, now fixed by the push, or persistent?).

### P3 — 2nd-generation bioenergy → land allocation (default-vs-switch axis)
> *Trace how 2nd-generation (lignocellulosic) bioenergy demand flows to land allocation in the
> **default** config: which module sets the bioenergy demand, how does it enter production, and what
> land type does it draw on? Is 2nd-gen bioenergy demand **exogenous or endogenous** by default?*

- Modules: 60, 17, 30, 10 · Docs: `module_60.md`, `module_17.md`, `module_30.md`
- **Lens check (default-vs-switch)**: must correctly state whether bioenergy demand is fixed
  exogenous by default (MANDATE 4 capability-vs-default).
- Touches M17 from a different direction than P1 (supply-side land draw vs demand-signal receipt).

### P4 — Income → diet → livestock demand (drivers chain, second axis)
> *In the **default** config, trace how a change in GDP/income per capita propagates to **livestock**
> product demand: which module holds the income driver, how does it alter diet composition, and which
> interface variable carries livestock demand into the production/trade balance? State whether the
> income→diet relationship is regression-parameterized or mechanistically optimized.*

- Modules: 09, 15, 70, 16 · Docs: `module_09.md`, `module_15.md`, `module_70.md`
- **Lens check (parameterization-vs-mechanism)**: diet-shift is parameterized (regressions on
  income) — a classic "uses data about X ≠ models X" trap. Answer must not call it mechanistic.
- Probes M09/M15 from the income axis (distinct from P1's population/quantity axis), so a shared
  failure across P1+P4 localizes the weakness to the driver layer itself, not one question's framing.

### P5 — Stale-module drift check (low stakes, two healthy-but-stale modules)
> *(a) Does MAgPIE track phosphorus by default, and if so which module handles it and what does it do
> with it? (b) In module 71 (livestock disaggregation), what is the default realization and what does
> it disaggregate? Cite the interface variable carrying disaggregated livestock to spatial units.*

- Modules: 54, 71, 70, 50 · Docs: `module_54.md`, `module_71.md`, `module_70.md`
- Purpose: confirm the R30–R32 doc push did not introduce drift into two modules that scored 9/8 and
  haven't been re-validated since. Expect high scores; a low score here = push-introduced regression.

### Regression anchor — **G4** (rotation: G4 last used R41, least-recent of the four)
From `validation_rounds.json.regression_questions` → G4 (magpie4 `getReport` dispatch structure).
Per validate-semantic.md §6, G3/G4 are load-bearing (they protect magpie4 version-pin discipline).
Set `drift_observed` per the expected_answer_summary. Append `44` to G4's `used_in_rounds`.

---

## 3. Dedup ledger reconciliation (`audit/probe_dedup_ledger.json`)

- **P2 (M20)**: last appended R27 → eligible. Clean.
- **P5 (M54 R28, M71 R22)**: eligible. Clean.
- **P1 / P4 (M09, M15, M16, M17)**: appended R41 → `retirement_eligible_after = 44`, i.e. at the
  boundary. **Accepted by design**: these are *intentional diagnostic re-tests* of known-weak modules
  — measuring whether the weakness persists is the point, so the recognition concern is subordinate.
  Mitigation: each probe targets fresh interface variables / a fresh causal axis (population vs
  income; demand-receipt vs land-draw), not the R41 framing. No specific locked variable/equation
  name from the ledger is reused.
- After the round: run `python3 scripts/probe_dedup_check.py --append-latest` (Step 5c).

---

## 4. Audit instrumentation — the lens bridge (what makes this diagnostic)

Auditors (Opus, per validate-semantic.md Step 3) read `audit/flywheel_rubric.md` for scoring as
usual, AND apply this round's two-axis bug classification:

**Axis 1 — root cause (existing schema taxonomy, unchanged):**
`doc_error` | `doc_error_answerer_beat_it` | `answerer_confabulation`

**Axis 2 — verifier_gap (NEW, this round; per-bug, optional):**
For every `answerer_confabulation` bug, record which verifier MANDATE (1–20 from
`agent/helpers/verifiers.md`) *should* have prevented it — e.g. a fabricated mechanism that a
parameterization claim should have caught → `verifier_gap: "MANDATE-4 (capability-vs-default)"`;
a wrong interface variable → `verifier_gap: "MANDATE-7 (variable-name lookup)"`. Leave null if no
existing MANDATE covers it (that itself is a finding: a coverage gap in the verifier set).

Record `verifier_gap` in each question's bug detail. This does NOT change the score — it is pure
diagnostic enrichment. It is the field that, aggregated across P1–P5, tells you whether the weak
area is a *content* problem (doc_error dominates → fix docs, done) or a *machinery* problem (one
MANDATE recurs as the gap → the verifier isn't firing for this module family).

---

## 5. Escalation decision (read AFTER the round, before doing more)

| Observed pattern | Interpretation | Next action |
|------------------|----------------|-------------|
| Bugs are mostly `doc_error`, idiosyncratic per module | Local content problem | Fix docs (Step 5), done. No lens audit. |
| Same `verifier_gap` MANDATE recurs across P1+P4 (driver layer) or P1+P2 (param-vs-mechanism) | Machinery problem: a verifier isn't firing for this module family | Run a **focused** lens audit on that ONE MANDATE's enforcement (not a full 6-lens `/pipeline-audit`) |
| `verifier_gap` null for several confab bugs | The verifier *set* has a coverage hole | Propose a new MANDATE; that's a machinery improvement, not a doc fix |
| Scores recover to ≥8 across the board | The R30–R32 doc push already fixed it; the all-rounds mean was just stale | Update current-quality figs; close the weak-spot item |

**Cost ordering rationale**: a full `/pipeline-audit` (6 parallel Opus lenses) just ran R8 (2026-06-03,
0 criticals, 15 findings — machinery healthy). Re-running it now is low-yield. This diagnostic
flywheel is the cheaper instrument that *tells you whether* a targeted lens audit is even warranted.

---

## 6. Expected resource cost

Per validate-semantic.md: ~5 Opus calls (audit) + ~10 Sonnet calls (answer + fix). ~45–60 min.
Targeted/diagnostic, so lighter than a full round if scores come back clean.

---

## 7. Run checklist

- [ ] Confirm next round number is 44 (`validation_rounds.json.cumulative_stats.total_rounds` was 43)
- [ ] Answer P1–P5 + G4 with Sonnet (docs only), 6 parallel agents
- [ ] Audit with Opus against GAMS source; apply §4 two-axis classification
- [ ] Apply the doc-error rule: every `doc_error` fixed this session regardless of score
- [ ] Read §5 escalation table before doing any further machinery work
- [ ] Record round in `validation_rounds.json` (type `targeted`); append G4 to `used_in_rounds`
- [ ] `python3 scripts/probe_dedup_check.py --append-latest`
- [ ] `bash scripts/validate_consistency.sh` (no syntactic regressions)
- [ ] Refresh `audit/tools/viz_validation_coverage.py` figures to reflect R44 results
