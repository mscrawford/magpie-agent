# R59 — PLAN (self-contained; written to be executed cold)

> **Future-self note: this file is self-contained.** Do not go looking for the morning
> conversation that produced it. Everything decided, derived, and verified is below.
> Where a number is stale or disputed, it says so — **re-derive those, do not copy them**.

**Status**: PARKED 2026-07-17 morning. Parameterized + designed, **nothing run**.
**Written by**: the parameterization session, at Mike's instruction ("lay this all out as a plan,
I'll get you started in the afternoon").

---

## 0. BINDING CONSTRAINTS (read before anything)

1. **Never push to `pik-piam/*` or `magpiemodel/*`.** Only `mscrawford` forks. Verify with
   `git remote -v` before any push. Ask before pushing at all.
2. **Never pool Arm A and Arm B scores into one mean.** They measure different things (§3, §4).
   A pooled mean is meaningless and would be a repeat of the 9.52 error.
3. **The round mean licenses NOTHING about corpus cleanliness.** See §1. This is not a caveat to
   soften — it is the round's central epistemic constraint, and it goes in the record verbatim.
4. **Do NOT edit AGENT.md's hub list this round.** Mike's explicit call (§6). Flag only.
5. **Fix agents must use `isolation: "worktree"`.** R58 lost work when three fixers shared one tree
   and two ran `git stash`. See [[feedback_concurrent_agents_shared_worktree]].
6. **Do not write the truth number** for the 3 unadjudicated dependent-count findings
   (`module_56.md:1138/:1150`, `module_17.md:899`) or `Module_Dependencies.md` — still held for Mike.

---

## 1. What this round is, and what it CANNOT license

QA round: question → answer-from-docs (Sonnet) → audit-against-GAMS (Opus). ~12 probes.
It samples **questions**, not the claim population.

**R58's caveat, restated so no future reader re-discovers it the hard way:**
R58's 4-question QA arm scored **8.375** on the same corpus where its depth arm found
**46 confirmed defects in 595 claims (7.7%)**. A QA mean over ~12 questions **structurally cannot**
detect a 5–8% claim-level defect rate.

So R59's mean licenses nothing about cleanliness. What it CAN do:
- **Arm A**: detect whether this morning's fix commits *broke* something or *left a Critical standing*.
- **Arm B**: probe real hubs that have **never** had a claim-level audit.

Power was raised 5 → 12 by Mike. That narrows the per-arm interval; it does **not** escape the above.

---

## 2. Mike's decisions (these are his calls, not mine — do not relitigate)

| Decision | Value |
|---|---|
| Agent | **magpie-agent** (not preproc — preproc's flywheel is R16, 2026-06-04) |
| Scope | **Split**: fix-verification arm + cold arm |
| Power | **Powered-up, 10–12 probes** (he overrode my power objection to the split) |
| Arm B basis | **Central + never-depth-audited (M35, M50, M52)** — not the coldest-by-recency peripherals |
| AGENT.md hub list | **Flag now, fix as a separate change** — do not touch it in this round |

---

## 3. Arm A — fix-verification (5 probes)

### Why it exists (verified this session)

The R58 record in `validation_rounds.json` (commit `71029ad`, 01:09) says:
> "The 39 surviving Major/Minor findings are documented and left for review."

**That is stale.** Commits at 07:07–07:20 the same morning applied them:

| Doc | Commit | Insertions |
|---|---|---|
| `module_11.md` | `77a666f` | 138 |
| `module_29.md` | `4d9bbb9` | 335 |
| `module_59.md` | `228b26c` + `2b74f9e` | 74 |
| `module_70.md` | `3791bd1` | 314 |

~720 insertions of **fix-agent-authored text, never validated**. Probes below were selected against
`git diff 71029ad..HEAD` hunk headers — they target the rewritten regions, not the docs generally.

**Correcting the R58 record is part of this round** (§7, Step 5b).

### Dedup status — deliberately violated

`probe_dedup_ledger.json` marks module_11/29/59/70 `retirement_eligible_after=51`, i.e. off-limits for
*fresh* probes because R58 just named them. Re-probing here is intentional (the R13 modality).
Consequence, and it is binding:
- **Arm A scores measure "did the fix hold", NOT capability.** Label them that way in the record.
- **Do NOT append Arm A module names to the ledger as fresh probes.**
  ⚠️ `probe_dedup_check.py --append-latest` auto-extracts `modules_tested` from the latest round —
  it will hoover up Arm A unless you intervene. Handle this explicitly at Step 5c; do not run it blind.

### Probes

| ID | Topic | Rewritten region probed | Modules |
|----|-------|------------------------|---------|
| A1 | Cropland carbon + age-class density chain | m29 `:779-841` | 29, 52, 32, 59 |
| A2 | Cropland total / available / fallow limit | m29 `:137-178`, `:370-382` | 29, 30, 10 |
| A3 | Feed balanceflow + scavenging + feed-scen default | m70 `:122`, `:416-453`, `:904` | 70, 71, 16, 17 |
| A4 | Livestock cost formation → M11 handoff | m70 `:269`, `:590`, `:825` | 70, 38, 11 |
| A5 | M11 cost aggregation set + M59 SOM → carbon stock | m11 `:185-253`, m59 `:194`, `:1049` | 11, 59, 52, 56 |

---

## 4. Arm B — central + never-depth-audited (5 probes)

### Why these, and why NOT the obvious "coldest" ones

My first design picked the coldest-by-recency modules: **M44 (R42), M40 (R43), M36/M37 (R43),
M20/M62 (R45)**. That design is **confounded and was discarded** — record why, so it isn't rebuilt:

Two memories independently assert **centrality predicts bug density**
([[project_magpie_r58_stale_hubs]]; 2026-05-30: *"central hubs ~6.2/doc with 4 Criticals; peripheral
hubs ~0 Criticals"*). M44/M40/M36/M37 are **degree 5–9 peripherals**. They would likely return
near-clean *because they are peripheral, not because they are cold* — a manufactured null that says
nothing about recency and invites exactly the "the cold corpus is fine" misreading this round exists
to prevent. Arm B must hold centrality roughly level with R58's hubs (M11=33, M32=29, M70=19, M29=19)
for any comparison to mean anything.

### The targets

| ID | Topic | Module | Degree / rank | Depth-audit history |
|----|-------|--------|---------------|---------------------|
| B1 | Natveg land dynamics → land balance | M35 | **22 / #3** | **NEVER claim-level audited** |
| B2 | Natveg carbon + age classes | M35 | 22 / #3 | **NEVER** |
| B3 | Soil N balance chain | M50 | **18 / #7** | **NEVER** |
| B4 | Inorganic fertilizer → cost handoff | M50 | 18 / #7 | **NEVER** |
| B5 | Carbon stock read + CO₂ pricing chain | M52 | 15 / #9 | R55 (bridge to R55's depth arm) |

Suggested spans (each ≥3 modules per rule #1): B1 → 35, 10, 52, 22 · B2 → 35, 52, 28, 32 ·
B3 → 50, 51, 18, 55 · B4 → 50, 11, 38, 17 · B5 → 52, 56, 59, 29.

**M14 (degree 18, #8) is excluded**: it is the G1 anchor and a fresh probe would collide with the
regression question. **M59 (18, #6) is excluded**: it is in Arm A.

The claim-level depth modality has only ever run on **M10/M32/M52 (R55)** and **M11/M29/M70 (R58)**.
M35 — the **#3 hub in the model** — has never been probed at depth. That is the gap Arm B fills.

---

## 5. Regression anchors (2)

**G1** (module-14 default realization) and **G3** (magpie4 version-pin discipline). Both last used
**R49** — the coldest pair. G2 (R52) and G4 (R50) are recent; skipped.

⚠️ **G3**: the auditor MUST read `project/version_pins.json` to compute the expected version/SHA.
Scoring against a hardcoded version is a rubric violation — the pin advances with upstream renv.lock.

---

## 6. FINDING TO REPORT TO MIKE: AGENT.md's hub list is probably wrong

`validate-semantic.md` question-design rule #4 says *"Bias toward high-centrality modules:
**11, 10, 56, 32, 30, 70, 17, 09**"*. Against the computed role map:

| In the list, but not a hub | Real hub, absent from the list |
|---|---|
| **M17 — degree 5, rank #33** | **M35 — 22, #3** |
| **M09 — degree 9, rank #22** | M29 — 19, #5 · M59 — 18, #6 · M50 — 18, #7 · M14 — 18, #8 · M52 — 15, #9 |
| M56 — 12, #13 · M10 — 13, #11 · M30 — 13, #10 | |

If real, every round following rule #4 was biased **toward** M17/M09 and **away from** M35/M50/M14 —
which is plausibly *why* M35 has never been depth-audited despite being #3. That makes it a
self-reinforcing survivorship mechanism in the round-design layer, one level above the survivorship
R58 found in the corpus.

**Do not act on this in R59** (Mike's call). Two reasons it needs corroboration before AGENT.md changes:
- The role map covers 139 interface vars with **13 `declared_in` nulls** — it may under-measure.
- R58 left **M17's dependent count unadjudicated** ("13 downstream" vs truth 12, entangled with
  `vm_prod`'s POPULATE/READ across 30/31/71/73). M17's degree-5 is exactly the disputed surface.

Treat as a **strong lead**, not a verdict.

---

## 6b. How the centrality numbers were derived (re-derive; don't trust the table)

**Command**: `python3 scripts/check_attribution_omissions.py --dump-rolemap`

**Two traps, both hit this session:**
1. **Two key conventions.** `declared_in` emits `"11_costs"` (directory name); `populated_by` /
   `read_by` emit `"11"` (bare number). Normalize with `^(\d{2})` **before** any set arithmetic, or
   `consumers = read_by - producers` silently fails to remove self-references and the declaring
   module becomes a phantom node. Un-normalized, M11 came out degree 53 with `produces=0`.
2. **"Degree" is a VARIABLE count, not a neighbour count.** R58's "degree 33 … produces 1, reads 32"
   is `|produces| + |reads|` over interface variables. Counting neighbouring modules gives a
   different, non-comparable metric.

**Working definition** (reproduces R58): normalize keys → `producers = populated_by ∪ {declared_in}` →
`reads = read_by − producers` → `degree = |produces| + |reads|`.

**Validation against R58's independently re-derived figures:**

| Module | This session | R58 | |
|---|---|---|---|
| M11 | 33, rank #1 | 33, #1 | ✅ MATCH |
| M32 | 29 | 29 | ✅ MATCH |
| M29 | 19 | 19 | ✅ MATCH |
| **M70** | **19** | **16** | ❌ **MISMATCH — unresolved** |

Also: M11 splits **2 produces + 31 reads** here vs R58's **1 + 32** — same total, one variable
classified differently. **Both discrepancies are open.** They do not change Arm B's selection
(M35/M50/M52 are not near the boundary), but if the afternoon session leans on M70's degree or on the
produces/reads split for anything, **re-derive first and resolve the delta** — do not inherit either
number. One of the two derivations is wrong and it is not yet known which.

---

## 7. Execution

- **Answer**: 12 × `magpie-helper`, **Sonnet**, docs-only, no raw GAMS. Prompt template in
  `agent/commands/validate-semantic.md` Step 2.
- **Audit**: 12 × `general-purpose`, **Opus**. Must read `audit/flywheel_rubric.md` before scoring.
  Must record `doc_errors_latent[]` per rubric §1.5 (answer right + doc wrong → fix regardless of score).
- **Fix**: **Sonnet**, `isolation: "worktree"` (constraint §0.5). Doc-error rule overrides the tiers:
  every `doc_error` / `doc_error_answerer_beat_it` is fixed this session regardless of score.
- **Gate**: `bash scripts/validate_consistency.sh` after fixes (expect 47 checks / 0 errors).
- **Record** (Step 5b): append R59 to `validation_rounds.json` — raw `mean_score` AND
  `doc_quality_mean`, **reported per arm, never pooled**, plus §1's licensing caveat.
  **Also correct the R58 record's stale "left for review" sentence** (§3) — cite the four fix commits.
- **Ledger** (Step 5c): `python3 scripts/probe_dedup_check.py --append-latest`, but see the Arm A
  warning in §3 first. Verify the script with `--self-test`.

**Cost**: 12 Sonnet answerers + 12 Opus auditors + fixers. This is the expensive part; it is why the
round was parked rather than started at 40% window.

---

## 8. Pre-flight (run these cold, before spawning anything)

```bash
cd <magpie-root>/magpie-agent
git status -sb                      # expect: branch r57-rolemap-guard, clean
git log --oneline -1                # expect: 4d9bbb9 (R58: apply module_29.md's 17 Major/Minor findings)
git -C .. log --oneline -1          # expect: 0d7ebeb90
bash scripts/validate_consistency.sh   # expect: 47 checks / 0 errors
```

⚠️ **If `../` HEAD is no longer `0d7ebeb90`, a /sync has landed and R58's coverage claims have
EXPIRED** ("Expires on the next /sync touching module .gms files"). Re-derive before relying on any
R58 figure, and reconsider whether Arm A's diff range (`71029ad..HEAD`) still isolates the fix commits.

## 9. Stopping criteria

- Stop after Step 5c (record + ledger). **Do not push** — ask Mike first (§0.1).
- If the gate goes non-zero and the cause isn't obvious in one pass: stop, report, don't improvise.
- If Arm A surfaces a **Critical in this morning's fixed text**, that is the round's headline —
  surface it immediately rather than completing all 12 probes first.

## 10. Expected artifacts

`audit/archive/rounds/round59_split/{PLAN.md, answers/, audits/, REPORT.md}` +
the R59 entry in `audit/validation_rounds.json` + the R58-record correction.
