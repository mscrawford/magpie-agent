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

---

## Update 2026-07-15 (build started — checker DONE + validated; corpus is HETEROGENEOUS)

**Built `scripts/check_attribution_tables.py`** — the deterministic phantom-attribution checker. It parses the "Provides To (Outputs)" / "Receives From (Inputs)" markdown tables and flags any row whose col-1 module references NONE of the row's interface vars in code (ground truth = `build_consumer_map`, a `\b`-anchored "referenced anywhere" set, so `.l` reads are not missed). Precision-first: phantom is the flagged direction; omissions are not flagged (the map over-lists).

**Validated three ways (fixture-first, per convention):**
1. Hermetic `--self-test` (injected ref-map): planted phantom flagged, correct rows clean. PASS.
2. **Real historical bug**: run against the PRE-R54 `module_32.md` (`git show 9d47e13:`), it flags M10 for `vm_landexpansion_forestry`/`vm_landreduction_forestry` and M35 for `pcm_land_forestry` (true refs = {32,58}) — i.e. it catches the exact R54 Critical class deterministically, in milliseconds.
3. Current corpus: 0 findings.

**The critical finding — the corpus "0 findings" is mostly BLIND, not clean.** A coverage control (instrumenting the real `scan_doc`) shows only **3/46 module docs** actually parse (module_32: 24 rows, module_10: 15, module_50: 15 = 54 rows total). **43/46 docs have a "Provides To/Receives From" header but 0 rows parsed** — because they express attribution as **prose**, not tables: bulleted "Module NN (name): `var`" lists (module_14), numbered "provides to these modules: N. Module 14: `var`" blocks (module_52), and bare inline "**Provides to**: Modules 52, 53, 51" (module_56, often with NO specific var). The table format that carried R54's Criticals is the MINORITY form.

**So the plan's "one mechanical pass covers the corpus" premise was too optimistic.** Deterministic coverage of the attribution class requires handling the prose forms too, which is bigger and FP-prone (negations like "NOT the yield calibration", var-less "provides to 13 modules"). `scripts/check_consumer_attribution.py` already has a partial prose handler (Pattern D: `PROSE_MODULE_NUM_RE` / `PROSE_MODULE_BARE_RE`) — the prose extension should build on and harden THAT, not start fresh.

**Status / next step:**
- `check_attribution_tables.py` is DONE, self-tested, and is real regression armor for the 3 table-format hub docs (32/10/50) + would have caught R54's Criticals. It is a standalone advisory (not yet wired into `validate_consistency.sh`'s gate, and its self-test not yet registered in `selftest_validator.sh` — both are the clean next increment; deferred to avoid gate churn at session end).
- **The corpus-measurement goal (turn "probably similar" into a number) is NOT yet met** — it needs the prose-form checker. That is the next build, and it is the larger, precision-sensitive half.
- Honest recalibration of the plan's cost line: this is not one cheap pass; it's (a) the table checker [done, cheap] + (b) a prose-attribution checker [the real work], each fixture-first with a positive control.

---

## Update 2026-07-15 (prose checker DONE + THE NUMBER — deterministic attribution measured)

**Built `scripts/check_attribution_prose.py`** — the prose complement to the table checker, closing the gap Check 31 left open (its `PROVIDES_RE` needs the module number *adjacent* to the verb, so the corpus's dominant labeled-bullet form `- **Module 10 (Land):** Provides \`fm_croparea\`` slipped through — that exact line was a real R54 Critical). Same direction-agnostic PHANTOM reduction the table checker uses (a module that references a var NOWHERE cannot provide/receive/read it, regardless of direction).

**Fixture-first, two positive controls both PASS:** (1) hermetic self-test, 17 cases incl. the 6 corpus FP classes locked in as regression controls; (2) the REAL pre-R54 `module_14.md` (`git show 9d47e13`) — flags exactly M10/`fm_croparea`, zero FPs on the other pairs.

**THE MEASURED NUMBER (deterministic, develop `0d7ebeb90`):**

| Checker | Coverage | Confirmed phantoms |
|---|---|---|
| `check_attribution_tables.py` (markdown tables) | 54 rows / 3 of 46 docs | 0 |
| `check_attribution_prose.py` (single-module prose) | **205 (module,var) pairs / 37 of 46 docs** | **2** |
| **Combined checkable attribution instances** | **259** | **2** |

→ **≈99.2 % of the deterministically-checkable single-module attribution instances are correct** (257/259). Raw prose flags were 8; manual + code triage → 6 false positives (negation, backticked-realization names, multi-var and multi-clause mis-binding), all eliminated by precision hardening and locked in as self-test negatives; 2 confirmed real.

**The 2 real bugs (both R54-class, both survived ~50 LLM rounds), fixed this session:**
1. `module_59.md:221` — `vm_nr_som_fertilizer` documented "provided to Module 51"; code shows it is consumed by **Module 50** (`50_nr_soil_budget/macceff_aug22/equations.gms:30`), never referenced in M51. Fixed → Module 50.
2. `module_73.md:698` — "Trade handled by Module 21 for aggregate `vm_prod`"; M21 references **`vm_prod_reg`** (3 realizations), never cellular `vm_prod`. Fixed → `vm_prod_reg`.

**HONEST SCOPE CAVEAT (what 99.2 % does NOT claim).** 205 is the UNAMBIGUOUSLY-PARSEABLE subset: exactly one "Module NN", exactly one backticked cross-module interface var (vm_/pm_/im_/pcm_/fm_), one `;`-clause. The checker deliberately SKIPS (precision-first): multi-module prose, multi-var clauses, var-less "provides to Modules 52, 53" forms, non-backticked mentions, and OMISSIONS (a real consumer missing from a list — the M58 class that actually hid in R54). Those remain LLM-audit / manual territory. So "99.2 % on the checkable subset" is a strong quality signal on the CLEANLY-STATED attributions and a proof the deterministic lever works (it found 2 reals the LLM missed) — it is NOT a bound on the whole attribution-error population. The omission direction, in particular, is the known blind spot and the natural next build.

**Harness wiring** (both checkers' `--self-test` in `selftest_validator.sh`; advisory non-gating hook in `validate_consistency.sh`, mirroring Check 31) is the cheap next increment — still deferred to avoid gate churn; proposed, not done.
