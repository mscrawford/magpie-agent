# Validate Documentation Consistency

**Purpose**: Run automated consistency checks across the documentation ecosystem.

**When user says**: "/validate", "check consistency", "validate docs", etc.

---

## How to Run

```bash
./scripts/validate_consistency.sh
```

The script runs **26 automated checks** across 11 categories:

1. **Dependency counts** — Same counts across files
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

- `scripts/validate_consistency.sh` — Script source (580 lines, 26 checks)
- `AGENT.md` — Document precedence hierarchy and link rules
