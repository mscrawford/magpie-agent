# R51 Phase C — Mechanical-coverage map

**Question**: of the load-bearing, code-checkable claim TYPES in the docs, which are verified by a **deterministic, LLM-independent** checker (so H1 holds by construction), and which are **LLM-only** (so H1/H2 is genuinely live)? This partitions where doc-correctness rests on the auditor's judgment vs on machinery that cannot be wrong in the same way.

Grounded in the docstrings of `scripts/check_*.py` and the 28 checks in `scripts/validate_consistency.sh` (read 2026-06-11), and the validation_rounds.json coverage ledger.

## Layer 1 — Deterministic, LLM-independent (H1-clean by construction)

These claim types are verified by code that indexes the GAMS source and does set-membership / equality checks. No LLM judgment; cannot share a blind spot with the doc author.

| Claim type | Checker | Catches (incl. these Phase-0 classes) |
|---|---|---|
| Identifier EXISTENCE (vm_/pm_/q/realization names) | Check 14/15/16/21 (`check_gams_variables/equations/realizations/doc_var_existence`) | fabricated variable/equation/realization (fixtures F3, F13, C9, C10, C12) |
| Default-realization LABEL vs config | Check 18 (`check_default_realizations`) | wrong realization as default (F1, C5, C6) |
| Parameter `(default N)` VALUE vs source | Check 20 (`check_param_defaults`) | inverted/wrong default WHEN the doc writes "(default N)" (F2, C7, C8, partial) |
| File:line citation existence (+content) | Check 17 / MANDATE 16 | citation drift (F5, partial — existence yes, "materially-different content" partial) |
| Consumer COUNT | Check 22 (`check_consumer_attribution`) | consumer-set COUNT drift (not source/identity) |
| Structural counts, deployment sync, conventions, links | Checks 1-13 | hardcoded count drift (RP5, partial), AGENT.md drift, format |

**Implication**: a large fraction of the Phase-0 planted classes (every fabricated-name and wrong-default fixture) is ALSO caught by Layer 1. The LLM auditor's catch on those is *redundant* with the mechanical layer — reassuring, but not its unique value.

## Layer 2 — LLM-only (where H1 vs H2 genuinely lives)

No deterministic checker can verify these; they require reading and reasoning about GAMS semantics. This is the auditor's unique contribution — and the only place a same-tier blind spot could hide a bug.

| LLM-only claim type | Example Phase-0 fixture | Why no mechanical check |
|---|---|---|
| A. Mechanism / parameterization-vs-mechanism | F4 (module-35 "fire from climate") | no checker parses whether a described mechanism matches the code's computation |
| B. Causal / data-flow DIRECTION between modules | RP6 (soilc serial vs parallel) | the direction of an inter-module arrow is not a token to index |
| C. Producer/populator vs consumer vs DECLARER identity | RP3 (manure "from Module 50"), RP2 (landcon) | Check 22 is COUNT-based; a right count with the wrong SOURCE module passes |
| D. Default-STATE caveat (active only under non-default switch/realization) | RP7 (M13 gated by c13_croparea_consv=0), RP4 (v21_trade non-default) | requires reading the `if`-gate / realization condition, not a label |
| E. Solution-level `.l/.lo` consumption | RP8 (vm_land sol-level reads) | presolve/postsolve attribute reads are invisible to equation-based count checks |
| F. Module attribution for COMPUTING a variable | F10, C11 (cost var owned by wrong module) | which module populates a var (vs consumes) is semantic |
| G. Prose index-domain / signature / arity | vm_tau (i) vs (j); vm_area dim truncation | explicitly UNMECHANIZED (BACKLOG: "Known low-EV gap ... prose parameter-arity / signature drift") |

## Layer 3 — Coverage (the actual residual risk)

Two coverage dimensions:

- **Doc-level LLM coverage: COMPLETE.** validation_rounds.json cumulative: 46/46 module docs + 33 non-module docs audited at least once (R30-R39 all-module push; R47 cross_module/core_docs capstone; R48-R50 conservation/Data_Flow/M56 re-audits). No whole doc is un-audited.
- **Claim-level coverage within docs: PARTIAL and is the residual.** A doc audited in round N had its *probe-focus* claims checked, not necessarily every Layer-2 claim. This is exactly how the replay bugs survived: RP3/RP4/RP5 sat in docs that HAD been audited, but the specific Layer-2 claim was not the probe that round, until a later FULL-doc audit caught it.

## Synthesis (with Phase 0)

The doc-correctness guarantee is a three-layer stack:
1. **Layer 1 (mechanical) is unconditionally clean** for existence / default-label / citation / count claim types — no LLM, no blind spot.
2. **Layer 2 (semantic) depends on the LLM auditor** — and Phase 0 showed it catches all seven Layer-2 classes at ~100% WHEN POINTED at the claim (per-claim regime), with code-grounded verification.
3. Therefore the residual risk is **Layer 3 claim-level coverage**: does a full-doc audit actually *reach* each Layer-2 claim? That is precisely what Phase B-prime measures (find-in-long-doc). If B-prime's find-rate is high, full-doc auditing closes the claim-coverage gap and H1 holds broadly; if it drops, the residual is real and concentrated in un-probed Layer-2 claims inside long docs.

**Where a stronger auditor (Fable/Mythos) would still add value**: only Layer 2 + Layer 3 — specifically the harder Layer-2 classes (B causal-direction, D default-state, E solution-level) embedded in long docs, and the unknown-unknown class beyond A-G. NOT Layer 1 (mechanical already covers it) and NOT per-claim Layer 2 (Opus already ~100%).

## Caveat

The Layer-1 checkers grep the **working tree**, not `origin/develop` (per the magpie-agent sync memory). So Layer 1's guarantee is "doc matches working-tree code"; if the working tree lags develop, doc-vs-develop drift escapes the mechanical layer until `/sync`. Minor here (develop is ~0 module-content commits ahead), but it means Layer 1 is "deterministic given the synced tree," not "deterministic vs upstream."
