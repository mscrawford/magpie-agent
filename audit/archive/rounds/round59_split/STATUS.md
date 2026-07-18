# R59 — STATUS (resume point; update after every phase)

**Purpose**: if this session dies, a fresh context resumes from HERE plus `PLAN.md` + `QUESTIONS.md`.
Do not reconstruct from conversation.

**Run started**: 2026-07-18 ~09:15, autonomous (Mike away, no mid-run decisions available).
**Branch**: `r57-rolemap-guard` · **magpie-agent HEAD at start**: `3496a53` · **parent HEAD**: `0d7ebeb90`

---

## PHASE LEDGER

| Phase | State | Evidence |
|---|---|---|
| 0. Pre-flight (§8) | ✅ DONE | see below |
| 1. Design 12 probes | ✅ DONE | `QUESTIONS.md` |
| 2. Answer (12 × Sonnet) | ✅ DONE | `answers/{ID}.md` — all 12, committed `8a09d78` |
| 3. Audit (12 × Opus) | 🔄 RUNNING | `audits/{ID}.md` |
| 4. Synthesize per-arm | ⬜ PENDING | `REPORT.md` |
| 5. Fix (Sonnet, worktree) | ⬜ PENDING | commits |
| 6. Gate + record 5b + ledger 5c | ⬜ PENDING | `validation_rounds.json` |
| 7. Report to Mike (NO PUSH) | ⬜ PENDING | — |

---

## PHASE 0 — pre-flight result (run cold 2026-07-18)

| Check | Expected (§8) | Actual | |
|---|---|---|---|
| parent HEAD | `0d7ebeb90` | `0d7ebeb9037c675f...` | ✅ **R58 coverage claims still valid; no /sync landed** |
| branch | `r57-rolemap-guard`, clean | same, clean, ahead 1 | ✅ |
| magpie-agent HEAD | `4d9bbb9` | `3496a53` | ⚠️ **benign** — `3496a53` is the parking commit that added `PLAN.md` itself; `4d9bbb9` verified as its parent via `git merge-base --is-ancestor` |
| validator | 47 checks / 0 errors | 47 checks / 45 passed / 2 warnings / **0 errors** / PASS | ✅ |
| `probe_dedup_check.py --self-test` | pass | `SELFTEST_OK` | ✅ |
| remote | `mscrawford` only | `origin git@github.com:mscrawford/magpie-agent.git` | ✅ no pik-piam/magpiemodel remote present |

**Arm A targeting verified**: every probe region cited in PLAN §3 appears in the new-side hunk
headers of `git diff 71029ad..HEAD` (m29 `+137`,`+178`,`+370`,`+382`,`+779`,`+841`; m70 `+122`,
`+416`,`+453`,`+904`; m11 `+185`,`+230`,`+253`; m59 `+194`,`+1049`). Diff range still isolates the
four fix commits (parent HEAD unchanged).

**§5 regression selection verified independently** against
`validation_rounds.json.regression_questions[].used_in_rounds`: G1 last R49, G3 last R49 (coldest
pair) · G2 last R52, G4 last R50 (recent, correctly skipped).

---

## FINDINGS RAISED DURING EXECUTION (for Mike; do not act without him)

**F-1 — `probe_dedup_ledger.json` is stale by ~6 rounds, and PLAN §3's dedup framing is off.**
- Max integer `retirement_eligible_after` in the ledger is **55** (implying last appended source
  round = **R52**). Rounds **R53–R58 were never appended** — Step 5c has been silently skipped again,
  the same failure mode the 2026-05-29 R27 maintenance note says was "FIXED".
- PLAN §3 states the ledger marks `module_11/29/59/70` as `retirement_eligible_after=51`, i.e.
  "off-limits". Two corrections: (a) `module_70` is **48**, not 51; (b) under the ledger's own
  `rotation_policy` (eligible *after* round N+3), a value of 51 or 48 at **R59** means those modules
  are **ELIGIBLE**, not off-limits.
- **This does not change the round.** PLAN §3's binding consequence — Arm A measures "did the fix
  hold", not capability, and Arm A names must not be appended as *fresh* probes — follows from the
  fact that R58 rewrote those docs hours earlier, not from the ledger. Constraint honoured as written.
- Backfilling R53–R58 is **out of scope** (§9 stops at 5c). Flagged for Mike.

**F-2 — AGENT.md hub list** (PLAN §6): flag only, not touched this round per §0.4.

**F-3 — §6b's M11 discrepancy is RESOLVED: R58 was right, and the role-map extractor has a
`.scale` false-positive bug.**
PLAN §6b left two deltas open ("one of the two derivations is wrong and it is not yet known
which"). I re-derived the role map cold this session with §6b's stated definition and reproduced
the parameterization session's table **exactly** (M11 33/#1 as 2 produces + 31 reads; M35 22/#3;
M50 18/#7; M52 15/#9; M29 19/#5; M59 18/#6; M14 18/#8; M70 19/#4). That agreement is **not**
corroboration — it is the same method run twice, so it inherits the same bug. Chasing the
disagreement instead:

- The role map lists `vm_cost_transp` as `populated_by: ["11"]`.
- Code truth: `vm_cost_transp` is DECLARED in Module 40 (`40_transport/off/declarations.gms:10`,
  `gtap_nov12/declarations.gms:13`) and POPULATED by Module 40 (`gtap_nov12/equations.gms:12` as
  equation LHS; `off/presolve.gms:9` fixes it to 0). Module 11 only READS it
  (`11_costs/default/equations.gms:21`, inside a `sum`).
- M11's **only** write-form occurrence is `vm_cost_transp.scale(j,k) = 1e3;`
  (`11_costs/default/scaling.gms:10`) — a **solver-scaling** statement, not population.

⇒ The extractor treats `NAME.scale(...) =` as population. **R58's M11 figure (1 produces + 32
reads) is correct; the plan's 2+31 is inflated by this bug.** Total degree 33 is unaffected (the
variable is counted either way), so **no Arm B selection changes** and PLAN §4 stands.

The **M70 19-vs-16 delta remains OPEN** — M70's `.scale`/`.fx` writes
(`fbask_jan16/scaling.gms:9-10`, `presolve.gms:9-11`) are all on variables M70 genuinely declares,
so this mechanism does not explain it; the M70 delta must sit on the read side, which I did not
re-derive. Arm B does not depend on M70's degree (§6b), so this was not chased further.

**Impact beyond this round**: the same `.scale` false positive likely inflates `populated_by`
elsewhere, which matters because the role map feeds both round-design centrality *and*
`check_attribution_omissions.py`. A producer/consumer set is exactly the R20 Critical anchor class.
**For Mike — not fixed here** (out of §9 scope).

**F-4 — partial blinding leak on probe B2.**
All 12 answerers were blinded from `round59_split/` (PLAN/QUESTIONS/STATUS/answers/audits) and from
`validation_rounds.json`, so no probe could see which regions R58 rewrote or which arm it was in.
B2's answerer, however, reported recovering the `m_carbon_stock` / `m_carbon_stock_ac` macro bodies
by grepping **archived round answers** (`audit/archive/rounds/round*` other than round59). That is
outside the blind but still prior-round material, so B2's score carries a small
recognition-vs-capability caveat. Its auditor was asked to check the underlying cause — whether
those macros are genuinely absent from all primary docs, which would be a real discoverability gap.
Not a re-run trigger; recorded so the score is read with the caveat attached.

**METHOD NOTE (applies to every Arm A/B score): auditors were blinded to arm membership.**
No auditor was told whether it was auditing a just-rewritten doc (Arm A) or a never-audited one
(Arm B). This keeps severity judgments from being biased by knowing R58 had touched the text hours
earlier. It does not change what Arm A scores MEAN (§3: "did the fix hold", not capability).

---

**F-7 — MAgPIE PARENT-REPO BUG: `c56_carbon_stock_pricing` is unreachable from config, and
Check 38 structurally cannot see it.** (Surfaced by B5's auditor as an aside; re-derived
independently here with a positive control.)

- **GAMS side (the switch is real and load-bearing)**:
  `modules/56_ghg_policy/price_aug22/input.gms:90` → `$setglobal c56_carbon_stock_pricing  actualNoAcEst`
  and `equations.gms:22` uses it inside the CO₂ pricing equation:
  `(pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))/m_timestep_length`
- **Config side (malformed)**: `config/default.cfg:1835` reads
  `c56_carbon_stock_pricing <- "actualNoAcEst"` — **missing the `cfg$gms$` prefix** that every
  sibling line carries (e.g. `cfg$gms$maccs <- "on_aug22"` at :1840).
- **Consequence**: the assignment creates an ordinary R variable in the config environment and is
  never passed to GAMS. **The switch cannot be set from config.** A user editing `default.cfg` to
  `"actual"` would silently keep getting `actualNoAcEst`.
- **Currently benign, latent**: config value and GAMS default are both `actualNoAcEst`, so no run is
  miscomputing today. It bites whoever first tries to change it — and this switch selects which
  carbon-stock slice is priced, so that is a high-stakes silent no-op.
- **Why the checker misses it**: Check 38 (`check_cfg_gams_wiring.py`, shipped by R58 for exactly
  this bug class) anchors on `CFG_SCALAR_RE = ^\s*cfg\$gms\$([sc]\d+_[A-Za-z0-9_]+)\s*<-`. It
  enumerates keys that HAVE the prefix and asks whether a GAMS identifier exists. A line MISSING the
  prefix is invisible to it. R58's three findings were *key present → GAMS identifier absent*; this
  is the **inverse subclass**: *GAMS identifier present → key malformed*.
- **Scope**: swept `default.cfg` for all GAMS-shaped identifiers assigned without the prefix
  (`^\s*[sc][0-9]{2}_[A-Za-z0-9_]+\s*<-`) — **exactly one hit**, this line. Isolated, not systemic.
- **NOT fixed here**: parent-repo change, out of §9 scope, and `magpiemodel` is push-forbidden.
  For Mike / the PIK briefing alongside R58's three dead keys.

---

**F-8 — PLAN §0.5 (`isolation: "worktree"`) and PLAN §7 (the gate) are IN TENSION. Resolved
procedurally; the plan should be amended.**

The harness creates the agent worktree **inside the repo** at
`magpie-agent/.claude/worktrees/agent-<id>/`, and it contains a **full 61-doc copy** of the corpus.
`scripts/validate_consistency.sh` globs recursively, so with a worktree present the gate reported
**53 checks / 7 errors / FAIL** — every error citing a worktree path, none citing the actual edit.
Removing the worktree restored **47 checks / 0 errors / PASS**.

Two further worktree limitations found in the pilot:
- The worktree checks out **only the magpie-agent repo, not the GAMS parent**, so `../modules`,
  `../config`, `../core` are absent. Checks 17-20 FATAL and 32-36 skip. **The gate can never run
  clean inside a worktree**, independent of any edit.
- Fix agents therefore have to reach *outside* the worktree to read GAMS ground truth anyway, which
  blunts the isolation the constraint was buying. (Reads are safe — nobody edits the parent.)

**Working protocol adopted** (honours §0.5's intent — no concurrent clobber — and §7's gate):
1. fix agent edits in its worktree (disjoint file set per agent);
2. merge its file(s) into the main tree;
3. `git worktree remove --force <path>` **and** delete the branch;
4. run the gate in the **main** tree only.

This is the R58 lesson's real shape: the hazard was *concurrent agents in one tree*, and disjoint
file ownership plus a no-git-mutation rule addresses it. Worktrees add isolation but cost the gate.
**Recommend amending §0.5** to "worktree isolation + mandatory teardown before gating", or to
"disjoint file ownership, no git mutations, sequential merge".

---

## PHASE 5 PROTOCOL (binding — from [[magpie_agent_lens_bridge_diagnostic]], R44/R48 lessons)

The doc-error rule AUTO-mandates a fix keyed on the **auditor's root_cause classification**. That
turns a mis-classification into a silent wrong edit. Two failure modes, both observed historically:

1. **R44**: auditors (even Opus) mis-tag. A `doc_error` tag was wrong twice in one round — the DOC
   was right and the ANSWERER conflated things. Blindly trusting tags would have edited two correct
   docs.
2. **R48**: the doc WAS wrong, but the auditor's recommended FIX would have INTRODUCED a new error.

**Therefore, before any fix agent edits anything:**
- Open the actual doc file and verify the classification's PREMISE, not just its conclusion.
- Verify the proposed FIX against code (`rg`, both `NAME(` and `NAME.` forms) — not just that a bug
  exists.
- Record `auditor_root_cause_corrections` in the round entry (R44 logged 1).

**Instrumentation gap I did NOT close this round (honest limitation)**: `verifier_gap` tagging —
labelling each `answerer_confabulation` bug with the `verifiers.md` MANDATE that should have caught
it — was not built into the auditor prompts. That is the designed escalation signal for
"machinery problem vs local gap". Not fabricated after the fact; noted as missing.

---

## BINDING CONSTRAINTS IN FORCE (from PLAN §0)

1. No push to `pik-piam/*` or `magpiemodel/*`; **ask Mike before any push at all**.
2. **Never pool Arm A and Arm B scores.** Separate means, always.
3. The round mean licenses **nothing** about corpus cleanliness (§1) — caveat goes in the record verbatim.
4. Do **not** edit AGENT.md's hub list this round.
5. Fix agents **must** use `isolation: "worktree"` (R58 lost work to shared-tree `git stash`).
6. Do **not** write the truth number for `module_56.md:1138/:1150`, `module_17.md:899`, or
   `Module_Dependencies.md` dependent counts — still held for Mike.
