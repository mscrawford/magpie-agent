# Validate Documentation Consistency

**Purpose**: Run automated consistency checks across the documentation ecosystem.

**When user says**: "/validate", "check consistency", "validate docs", etc.

---

## How to Run

```bash
# 1. Prove the guard itself works (positive control). REQUIRED before trusting
#    any "clean" result — a validator that can't fail is not evidence of health.
./scripts/selftest_validator.sh    # must print SELFTEST_RESULT: PASS

# 2. Run the validator.
./scripts/validate_consistency.sh
```

**Trustworthiness protocol (read this — it is why the validator was dead for ~7 months without anyone noticing):**

- A run is only valid if it reaches the `VALIDATOR_RESULT:` line containing `completed=1`. Anything else means the run ABORTED (exit 99) and the result is **invalid** — do NOT record it as a pass.
- Exit codes: **0** = PASS (completed, 0 errors), **1** = FAIL (completed, errors > 0), **99** = ABORTED (never completed — the guard is broken, not necessarily the docs).
- When recording a result in `project/sync_log.json` or a PR description, **paste the `VALIDATOR_RESULT` line (or `.cache/validation_reports/latest_result.json`) verbatim**. Never hand-type "NN/NN clean" — that is exactly how a green that no completed run produced ended up in the history.
- CI enforces this on every push/PR via `.github/workflows/validate.yml`: the self-test and abort-detection are always blocking; doc drift is advisory until the repo variable `VALIDATOR_STRICT=true` is set.

The script runs **a suite of top-level structural checks (each with sub-checks)** across these categories (the run's `VALIDATOR_RESULT` line prints the live counts; the script is the single source of truth for the full list, which now extends past those below):

1. **Dependency counts** — Same counts across files (Modules 10, 11, 17)
2. **Equation parameters** — Consistent descriptions
3. **Cross-references** — All linked files exist
4. **Duplicate equations** — Matching formulas
5. **Entry points** — README/AGENT.md/sync_log.json
6. **File counts** — Expected file inventory
7. **Naming conventions** — No stale `/command:` format refs, no stale CLAUDE.md refs
8. **Markdown links** — All link targets exist
9. **Trigger keywords** — Helper triggers match AGENT.md routing table
10. **AGENT.md deployment** — Source and deployed copy in sync
11. **Hardcoded values** — No hardcoded commit hashes in mechanism files
12. **Stale path prefixes** — No magpie-agent/ prefixes in backtick-quoted paths (project-relative form only)
13. **Unclosed code blocks** — All fences balanced
14. **GAMS variable names** — Backtick-quoted vm_*/pm_*/v<N>_*/etc. resolve to declarations.gms
15. **GAMS equation names** — Backtick-quoted q<N>_* resolve
16. **GAMS realization names** — Month-format realization names resolve to existing directories
17. **File:line citations** — Cited lines within file EOF
18. **Default realization labels** — Doc claims match config/default.cfg

## What to Do with Results

**Errors (❌)**: Fix immediately — broken links, missing files, contradictory numbers.

**Warnings (⚠️)**: Review — may be acceptable variation (e.g., different phrasing for same concept).

**Precedence for fixes**: Code > module_XX.md > cross_module/ > core_docs/ > notes files.

The script generates a timestamped report file — delete it after reviewing.

## When to Run

- After adding or modifying documentation files
- After `/sync` updates module docs
- As periodic maintenance (weekly/monthly)
- Before committing documentation changes

## See Also

- `scripts/validate_consistency.sh` — Script source (run it to see the live check list)
- `AGENT.md` — Document precedence hierarchy and link rules
