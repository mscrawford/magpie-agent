# Validate Documentation Consistency

**Purpose**: Run automated consistency checks across the documentation ecosystem.

**When user says**: "/validate", "check consistency", "validate docs", etc.

---

## How to Run

```bash
./scripts/validate_consistency.sh
```

The script runs **<!--count:validator_main_checks-->25<!--/count--> top-level checks (<!--count:validator_sub_checks-->40<!--/count--> sub-checks total)** across these categories:

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

- `scripts/validate_consistency.sh` — Script source (<!--count:validator_main_checks-->25<!--/count--> checks)
- `AGENT.md` — Document precedence hierarchy and link rules
