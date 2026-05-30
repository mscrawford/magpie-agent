# Overnight doc-improvement push — magpie-agent — 2026-05-29

**Autonomous run** (user asleep). Plan: `~/.claude/plans/flickering-humming-sutherland.md`.
3 hybrid flywheel rounds (R30/R31/R32), 10 docs each, Opus-Max audits / Sonnet fixes.
**NOTHING PUSHED** — all commits local, pending user review.

- Start: 2026-05-29 22:12 Berlin (UTC 20:12). caffeinate -t 28800 (expires ~06:12 Berlin).
- magpie-agent start HEAD: `bcdf663` (main). Develop worktree (verification truth): `/tmp/magpie_develop_ro` @ `ee98739fd`.
- Lock: `/tmp/magpie_docpush.lock`.

## Baseline gate (pre-run)
- `validate_consistency.sh`: **0 errors**, 2 warnings (GREEN).
- `check_units.py` advisories (leads for auditors): module_60:557 vm_dem_bioen, module_57:375 s57_step_length, module_12:825 pm_interest (claims 'TC' vs '% per yr'), module_56:1031 vm_cdr_aff, module_39:578 vm_cost_landcon.
- `check_consumer_attribution.py` advisories: module_52:291 pm_carbon_density_plantation_ac_uncalib lists M35 (no grep-hit — possible phantom); module_16:568 vm_supply omits M70.

## Status
| Round | Scope | State | mean / doc_quality | bugs (C/Ma/Mi) | commit |
|------|-------|-------|--------------------|----------------|--------|
| R30 | hub + cross-module | ✅ done, committed (local) | 7.0 / ~7.0 (anchors G2,G3=10, no drift) | doc-audit 2C/17Ma/19Mi confirmed+fixed (51 edits, 10 docs); gate clean | local |
| R31 | coverage-gap modules | ⚠️ partial, committed (CAP-degraded) | anchors G1,G4=10 no-drift (q-probes lost to cap) | doc-audit 5C/3Ma/5Mi fixed in 5/10 docs (29 edits); 5 docs dropped → recovered in R32 pass | local |
| R32 | ref/helpers + R31-recovery | ✅ done, committed (local) | doc-centric (no q-probe), 22.6 min, 0 dropped | 1C/35Ma/24Mi fixed, 13 docs, 86 edits; gate clean; magpie4_reference + maintenance_protocol CLEAN | local |

**R31 highlights:** consumer-set Criticals keep coming — module_55 (3 Critical: vm_manure_confinement vs vm_manure conflation, M50/M51 omissions), module_12 (Critical: pm_interest listed 3 consumers, code has 9), module_13 (Critical: M38 phantom vm_tau consumer, transitive via vm_yld). module_09 M13 "GDP drives adoption" gloss confirmed+fixed. Two fed advisories correctly REFUTED (module_12 'TC'=abbreviation not unit; module_13 already correct) — good false-positive discipline.

**R30 highlights:** module_10.md had 8 more consumer-set/citation bugs beyond R29's 2 (5 Major). Data_Flow.md DF-1 Critical: phantom M56 + omitted M14 in carbon-system consumer set. modification_safety_guide.md: 1 Critical centrality claim. Core_Architecture doc-audit found it clean, but the question-probe caught 2 latent doc errors it missed (hybrid value). Spot-check: modules 14/71/80 confirmed zero vm_land refs in develop (module_10 table fix correct).

## Mid-cycle compute probe (after R30)
- R30 actual: **35.9 min** wall-clock, 45 agents, **0 dropped**. Output tokens 536k (Opus 463k + Sonnet 73k); non-cache-read ~10.6M; all-category incl. cache reads 163.8M.
- **Max inter-message gap: 1.62 min** (< 5 min) → **r30_capped = FALSE**. No rate-limit wait; headroom ample.
- Extrapolation: 3 hybrid rounds ≈ 108 min, projected finish ~00:45 Berlin (large margin before morning). R30's ~10.6M did not approach the rolling window cap.
- **DECISION: R31 = hybrid. Re-probe after R31; trim R32 to doc-centric-only only if R31 shows capping.** (Even if a cap hits later, it pauses+resumes with the host kept awake; completion stays intact.)

### Re-probe after R31 — CAP HIT (this is why the mid-cycle test matters)
- R31 wall-clock **202 min** (vs R30's 36), max inter-message gap **187.8 min** — a single ~3h rate-limit wait. The rolling window was exhausted (R30 ~10.6M + R31's start), agents that ran later errored to null.
- Damage: 5/10 doc-audits dropped, all 10 q-probes lost. Anchors survived (ran early). The disk-first + .catch isolation meant the 5 completed doc-audits + fixes + anchors were preserved and committed — **zero completed work lost**, exactly the cap-resilience design goal.
- Window appears to have reset ~02:00-02:30 Berlin (the 3h wait ended at 02:33). 
- **ADAPTIVE DECISION: R32 → doc-centric-only (no q-probe: the cap-vulnerable, lower-value half), and FOLD IN R31's 5 dropped docs.** One lean 15-doc-audit workflow instead of two hybrid rounds — minimizes agents under the cap while recovering all dropped coverage. Anchors skipped (all four G1-G4 already exercised clean across R30+R31).

## Decisions / deferrals
- R31 = hybrid (10 module docs: 09,12,13,55,45,62,28,58,53,57). R32 mode set by the post-R31 re-probe.
- Baseline advisory triaged: `module_52.md:291` "M35 consumer" = **FALSE POSITIVE** (checker matched a co-located "Module 35" tied to an adjacent parameter; doc is correct) — confirmed in smoke + R30. `check_consumer_attribution.py` has a co-located-name FP mode (note for maintainers; out of scope tonight).
- Fixers introduced 7 bare-basename .gms citations; the syntactic gate (check 25/27) caught and corrected all to full paths → 0 errors. The gate handles this class automatically each round.
- R30 deferred-for-review (non-code-verifiable, NOT edited): graph aggregates in Module_Dependencies (edge counts, "173 dependencies", "26 cycles"); runtime/input-derived counts in Data_Flow (.cs3/.mz file counts, cell counts). See each `round30_docaudits/*.md` `deferred`.

## FINAL SUMMARY — all three rounds complete (finished ~03:00 Berlin 2026-05-30)

**30 distinct at-risk docs audited against origin/develop @ee98739fd; 111 confirmed doc bugs fixed in 166 edits across 26 files. Gate clean throughout (0 errors). Nothing pushed.**

| Round | docs | confirmed doc bugs | edits | commit | note |
|------|------|--------------------|-------|--------|------|
| R30 hybrid | 10 (hub + cross-module) | 2C / 17Ma / 19Mi | 51 | `2c627e2` | full hybrid; mean 7.0; anchors G2,G3=10 |
| R31 hybrid (partial) | 5/10 (modules) | 5C / 3Ma / 5Mi | 29 | `7512f5d` | **cap hit** (~3h wait); 5 docs + all q-probes dropped; anchors G1,G4=10 |
| R32 doc-centric | 15 (5 R31-recovery + ref/helpers) | 1C / 35Ma / 24Mi | 86 | `9dcc386` | cap-adaptive lean pass; recovered all R31 drops; 0 dropped |
| finalize | — | — | — | (this) | validation_rounds.json→schema 1.4, ledger, rubric note |

**Totals: 8 Critical + 55 Major + 48 Minor = 111 confirmed doc bugs fixed.** All four regression anchors (G1-G4) exercised, **no drift**.

**The thesis held:** the dominant vein was wrong consumer/populator sets + citation drift in hub/cross-module/module docs — and it was NOT exhausted. Critical/Major consumer-set bugs found in module_10 (8 beyond R29's 2), Data_Flow (phantom M56), module_55 (3), module_12 (pm_interest 3-vs-9), module_13 (M38 phantom), module_57 (vm_maccs_costs), module_28 (3 omissions). Several fed advisories were correctly **refuted** (module_12 'TC', module_28 ac300, module_57 unit) — good false-positive discipline; the grep-guard + positive-control method held.

**The mid-cycle probe earned its keep:** it empirically caught the R31 cap (max gap 188 min) and rerouted R32 to a lean doc-centric config instead of blindly firing another 45-agent hybrid — which is why R32 completed in 22 min with zero drops.

**What was sacrificed to the cap (candidates for a follow-up pass):** R31's 10 question-probes (the trend-continuity half) were lost; R32 ran doc-centric (no q-probes). The doc-audits (the high-value half) covered all 30 docs. Per-doc deferred (non-code-verifiable) items are in each `round{30,31,32}_*record.json` and the `round*_docaudits/*.md` reports.

## Morning checklist for the user
- Review per-round commits on `main` (NOT pushed): `git -C magpie-agent log --oneline bcdf663..HEAD`
- Per-round detail: `audit/archive/rounds/round{30,31,32}_*`
- Deferred (uncertain) findings: see each round_record.json `deferred_for_review[]`
- If satisfied: push to mscrawford on your go.
