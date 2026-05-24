#!/usr/bin/env python3
"""Check 25 — forbid bare-basename .gms citations in non-module docs.

A bare cite like `equations.gms:20` is ambiguous in cross-module / helper /
reference docs (which module's equations.gms?). After the 2026-05-24 migration
(scripts/migrate_bare_cites.py) these should always be full-path:
`modules/NN_name/REAL/file.gms:N`.

This check enforces that invariant going forward.

Scope: cross_module/, core_docs/, reference/, agent/helpers/, AGENT.md, README.md
Exempt: modules/module_NN.md and _notes.md (context is the module itself)

Allowlist markers (for intentional pedagogical examples):
  Whole-doc: `<!-- check-bare-cites: allow -->` anywhere in the doc
  Per-line:  `<!-- check-bare-cite -->` on the same line as the cite

Usage: python3 check_no_bare_cites.py [--summary-only]
Exit:
  0 if no bare cites (or all are allowlisted)
  1 if violations found
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent

# Same bare-cite regex as migrate_bare_cites.py
BARE_RE = re.compile(r"(?<!\w)(?<![./])(?P<file>\w+)\.gms:(?P<line>\d+)")

SCOPE_PATTERNS = [
    "cross_module/*.md", "core_docs/*.md", "reference/*.md",
    "agent/helpers/*.md", "AGENT.md", "README.md",
]

WHOLE_DOC_ALLOW_RE = re.compile(r"<!--\s*check-bare-cites:\s*allow\s*-->")
PER_LINE_ALLOW_RE = re.compile(r"<!--\s*check-bare-cite\s*-->")


def scan_doc(doc_path: Path) -> list[tuple[int, str]]:
    """Return list of (lineno, cite_text) for unallowlisted bare cites."""
    text = doc_path.read_text(encoding="utf-8", errors="ignore")
    if WHOLE_DOC_ALLOW_RE.search(text):
        return []
    violations = []
    for i, line in enumerate(text.splitlines(), 1):
        if PER_LINE_ALLOW_RE.search(line):
            continue
        for m in BARE_RE.finditer(line):
            before = line[: m.start()]
            if "modules/" in before[-40:] or "core/" in before[-10:]:
                continue
            violations.append((i, m.group(0)))
    return violations


def main() -> int:
    summary_only = "--summary-only" in sys.argv

    docs: list[Path] = []
    for pat in SCOPE_PATTERNS:
        docs.extend(sorted(AGENT_DIR.glob(pat)))

    all_violations: list[tuple[str, int, str]] = []
    for doc in docs:
        for lineno, cite in scan_doc(doc):
            all_violations.append((str(doc.relative_to(AGENT_DIR)), lineno, cite))

    print("Bare-basename .gms citations in non-module docs")
    print("================================================")
    print(f"Docs scanned: {len(docs)}")
    print(f"Bare cites found: {len(all_violations)}")
    print()

    if not all_violations:
        print("✅ No bare cites in non-module docs (all use full-path form)")
        return 0

    print(f"❌ Found {len(all_violations)} bare cite(s):")
    if summary_only:
        from collections import Counter
        counts = Counter(v[0] for v in all_violations)
        for doc, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {doc}: {n}")
    else:
        for doc, lineno, cite in all_violations:
            print(f"  {doc}:{lineno}  {cite}")
    print()
    print("Fix: rewrite as `modules/NN_name/REAL/file.gms:N` (run scripts/migrate_bare_cites.py).")
    print("If intentional (pedagogical example), add:")
    print("  `<!-- check-bare-cites: allow -->` to exempt the whole doc, OR")
    print("  `<!-- check-bare-cite -->` to exempt a single line.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
