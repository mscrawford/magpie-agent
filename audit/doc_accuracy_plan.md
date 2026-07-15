# Plan: get doc-CLAIM accuracy under control (the cross-module attribution class)

**Status:** PROPOSED, awaiting user go/no-go. **Written:** 2026-07-15, after R54.
**Supersedes nothing; complements** `get_under_control_plan.md` (the May "bomb rate" plan, largely executed) and directly engages the **2026-06-29 freeze** (`[[project_magpie_agent_initiatives]]`, `BACKLOG.md`).

---

## The finding that triggered this (measured, not asserted)

R54 deep-audited 5 docs rewritten during the 2026-07-14 sync and found **7 Criticals + 30 Majors**, almost all in OLD sections. Git blame dates the Criticals to the **original authoring (2025-10-13 / 2025-10-22)** — ~9 months old.

The uncomfortable part is not that they existed. It is that **they survived repeated deep audits**:

| Doc | Prior deep doc-vs-code audits it passed | R54 Critical it still carried |
|---|---|---|
| module_32 | **R33** (2026-05-30, high-centrality hub deep audit) | Module 58 absent from the cross-module graph; 4 interfaces mis-attributed to M10/M35 (M58 is their sole consumer) |
| module_14 | **R33** (same) | `fm_croparea` attributed to M10 (declared in M30); a fabricated M14↔M17/M55/M59 dependency cycle |
| carbon_balance | **R30, R47, R48, R49** — R49 used THIS SAME `doc_audit_round.workflow.js` engine | "Peatland Carbon Not Modeled" — false; M58/v2 (default) models it |

And the corpus wide-net pass on **2026-06-29 scored 9.52** (46 docs → 2 real bugs), which grounded the "doc accuracy is solved" freeze. That score could not see this class.

## The diagnosis: this is FNR-limited, not coverage-limited

The docs were **covered** — multiple times, by the same class of instrument. What failed is the **per-pass false-negative rate on cross-module attribution claims** (who DECLARES / POPULATES / READS an interface variable). That class is:

- **The most common bug class** (R30–R37 sweep: producer/declaration ~30% + consumer-set ~28% = **~58% of all bugs found**) AND the most-missed — it is the R20 Critical anchor.
- **Correlated-confabulation-prone**: LLM auditors re-derive consumer sets under a shared prior and hallucinate the same omission, so more LLM verifiers do NOT drive the FNR to zero (`[[feedback_correlated_confabulation_mechanical_checks]]`). R51 exists precisely because we measured this auditor FNR.
- **Invisible to a doc-side check**: verifying "`vm_land_forestry` is real and M32 produces it" passes without ever testing "who CONSUMES it" — so a wrong consumer attribution reads as correct unless you enumerate from the CODE side and notice an omission.

R54 caught them through a combination that lowered the FNR — **fewer docs/round (~520k tokens/doc vs R33's 12-docs-per-round), the fully-hardened engine (adversarial verify + the producer rule added this session + both-endpoints grep), and DIRECTED advisories** ("re-derive every interface-ownership claim; hunt fabricated dependencies") — plus, honestly, **stochastic variance**: the same doc audited 4 times can miss the same Critical thrice and catch it once.

**Conclusion:** running the LLM doc-audit yet again, even deep, is not the fix — it has a floor FNR on this class. The lever is **mechanical enumeration**.

## The lever: mechanize the CONSUMER/READ-BY half of attribution

The repo already has `scripts/check_role_attribution.py` (Check 31, added at the 2026-06-29 freeze) — but it only mechanizes MANDATE 18's **DECLARED** half (the FP-safe part). Every R54 Critical was in the **CONSUMER / READ-BY / "provides-to"** half, which is NOT mechanized. That is the precise, actionable gap.

**Proposed (ONE focused piece of machinery, targeting the severe class):** a deterministic checker that, for every interface variable (`vm_*`, `pm_*`, `im_*`, `pcm_*`), computes the true set from develop —
- **DECLARED-IN**: the module whose `declarations.gms` names it (already done by Check 31);
- **POPULATED-BY**: modules with it on an equation LHS / `.fx` / assignment;
- **READ-BY**: modules that reference it (`NAME(` AND `NAME.` attribute forms — the both-endpoints grep guard, so `.l/.lo` reads are not missed) —

and **diffs that ground-truth set against each doc's "Provides To / Receives From / consumers" tables**, flagging phantom members AND omissions (an omission is what hid Module 58). Deterministic → ~0 FNR on exactly the class that 4 LLM audits missed. Emits file:line for each discrepancy.

This is **not a safari** (it hunts one severe class, not all bug types) and **not validator proliferation** (it extends the existing Check-31 attribution checker to its missing half) — so it is compatible with the letter and spirit of the freeze, which itself permitted the Check-31 mechanization.

## Proposed sequence (each step gated on the prior; user go/no-go at ⭑)

⭑ **0. Decision.** This plan asserts the freeze's premise ("9.52 = solved") is undermined **for the attribution class specifically**. The freeze remains correct for low-severity classes (citation drift, count drift — genuinely diminishing returns). User decides whether to act on the attribution class now or defer.

1. **Build the READ-BY/POPULATED-BY checker** (extends `check_role_attribution.py`). Follow the mandatory convention: **synthesize a known-bug fixture FIRST** (plant a wrong consumer, confirm the checker flags it) before running on the corpus — else "0 findings" is ambiguous (`[[synthesize-known-bug-test-for-new-validator]]`). Positive control is non-negotiable (R54 proved it).
2. **Run it corpus-wide** (all 46 module docs + cross_module/). Deterministic, cheap — this is the whole point; it replaces ~27M tokens of repeat LLM audits with one mechanical pass.
3. **Triage output**: mechanical flags → confirm each against develop → fix by explicit path → gate. The high-centrality hubs (M10, M52, M56, M21, M70) are the priors for density (centrality predicts bug density — R33 finding).
4. **Re-derive the true doc-accuracy baseline** on the attribution class, and record it SEPARATELY from answer-quality scores, so no future "9.52" is misread as "all claims verified."

## What stays as-is (do NOT reopen)

- **The seatbelt**: drift-triggered LLM rounds on docs the agent JUST WROTE stay load-bearing (`[[project_magpie_agent_initiatives]]` 2026-07-14). R53 + R54's module_32_notes over-correction prove fresh content self-injects defects a syntactic gate cannot see.
- **The freeze on low-severity safaris and new-validator proliferation** for classes OTHER than attribution.
- **Positive control every doc round**, and **score the DOC not the answer**.

## Cost

Step 1: one session (checker + fixture + self-test). Step 2: ~free (mechanical). Step 3: scales with findings — if the attribution FNR is as high as R54 suggests, expect a multi-session fix backlog concentrated in the hubs, but each fix is a cheap explicit-path edit, not a token-heavy audit. This is the cheap-high-info move: **replace repeat LLM audits (high FNR, high cost) with one deterministic enumeration (zero FNR, near-zero cost).**

## Open threads this does NOT close

- Batch 2 of R54 (module_22, 3 reference docs, debugging_gams_errors helper) — the LLM doc-audit half, still worthwhile for NON-attribution classes on those specific just-touched docs.
- Lead A materiality (needs a model run) — unrelated to this plan.
