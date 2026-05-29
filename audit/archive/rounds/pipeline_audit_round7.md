# Pipeline Audit Round 7 — Report: CONSOLIDATION

**Date**: 2026-05-29 | **Design**: `pipeline_audit_round7_design.md` | **Auditor**: claude-opus-4-8, 6 find + 7 verify subagents

## Result

**40 findings** (4 HIGH, 19 MEDIUM, 17 LOW) across the 6 consolidation lenses. 13 removal/merge
candidates deduped to **7 unique artifacts**, each adversarially verified.

By action: 4 delete, 5 retire, 4 merge, 13 simplify, 6 fix-incoherence, 5 keep-document-only, 3 backfill-test.

### Adversarial verdicts (the removal gate)

| Artifact | Verdict | Note |
|---|---|---|
| `add_timestamps.py` | confirm_safe_to_remove | dead + would corrupt footers if run |
| `pr_*.py` trio (x2 lenses) | confirm_safe_to_remove | ~1192 LOC, deep-shelf, 0 catches |
| `check_gams_equations.sh` | confirm_safe_to_remove | byte-identical twin of the .py |
| `check_gams_realizations.sh` | confirm_safe_to_remove | weaker divergent twin; feeds wrong count |
| `check_gams_realizations.py` | partial_keep_some | KEEP .py, retire the .sh |
| `check_default_realizations.py` (Check 18) | **partial_keep_some (REFUTED merge)** | synthesized test proved Check 18/19 catch DISJOINT classes; overlap form used by 0 docs |

### Refutations (what the verify stage stopped)
- **Check 18 NOT merged into Check 19** — the verifier built a synthesized known-bug test showing they catch disjoint classes; the "overlap" header form is used by 0 docs.
- **No MANDATE demoted** — none is fully mechanized; every check-backed MANDATE has a documented coverage gap, so demotion would drop the answer-time guard.
- **`check_gams_citations.sh` kept** — genuine thin wrapper around `_impl.py`, not a duplicate.
- **Live, not dead**: `probe_dedup_check.py`, `advisory_allowlist.json`, `audit/integrated/`, `sync_magpie4_clone.py`.
- Gate wall-clock (4.0s) and content-mismatch FPs (0) are fine — not padded.

## Interventions (40 findings -> 6 root-cause clusters)

| # | Intervention | Status | Commit |
|---|---|---|---|
| I1 | Collapse dual `.sh`/`.py` GAMS checkers to one `.py` (delete 3 `.sh`; repoint refresh; drop dead gate fallbacks) | APPLIED | `65f6718` |
| I2 | Remove dead scripts: `add_timestamps.py`, `pr_*` trio, `audit/templates/` | APPLIED | `a3079b7` |
| I3 | Retire the aggregate-count marker system (2 scripts + Check 27 + 14 markers; print_section auto-numbers) | APPLIED | `be17620` + `717cd78` (AGENT.md) |
| I4 | Coherence fixes (MANDATE 16->17, README/BACKLOG round-ranges, schema 1.2->1.3, R26 status) + hedged-claims FP fix | APPLIED | `d82d50b` + `717cd78` |
| I5 | Check-retirements (Checks 1/2/4/6/23/26) + bare-basename advisory silence | **DEFERRED** | follow-up |
| I6 | Backfill self-tests for 3 surviving load-bearing checks (Check 17 citations, Check 18 default-real, Checks 14/21 var/doc-var) | **DEFERRED** | follow-up |

## Net effect
~7 scripts + ~1,900 LOC + a whole gate check + the marker subsystem removed; killed a LIVE
count drift; 28 hardcoded `/28` denominators collapsed to one self-counting var; ~900 computed
advisory lines/run eliminated (markers + hedged). Gate went 28->27 checks, 4->2 warnings,
**0 errors throughout** (verified after every cluster).

## Deferred to a follow-up round (per user, 2026-05-29 — session length)
1. **Check-retirements** (Checks 1/2/4/6/23/26; delete `check_units.py` + `check_multi_section_consistency.py`). Now LOW-risk (print_section auto-numbers; just delete the block + decrement `SECTION_TOTAL`). LOW value (these checks catch ~nothing). Keep Checks 3 + 8 (real link integrity).
2. **Bare-basename advisory silence** — `check_gams_citations_impl.py` still computes ~779 non-actionable bare-basename advisories/run for module docs (redundant with Check 25). Touches the load-bearing 71%-bug-class checker — needs a careful edit + diff, not an end-of-session change. (See also BACKLOG "Bulk bare-basename citation cleanup".)
3. **Self-tests (I6)** for the 3 surviving load-bearing checks with proven silent-failure histories. Additive (against the delete-bias) but justified per `feedback_test_the_testers`.
4. **`get_under_control_plan.md` archival** — the R24 campaign is complete; the file is archive-ready (move to `archive/plans/` + sweep ~6 cross-references). Status updated in place this round; the move is deferred.
5. **Dead skip-globs** in `validate_consistency.sh` (BACKLOG-flagged at ~:381/:422-425/:631).
