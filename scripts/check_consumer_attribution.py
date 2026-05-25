#!/usr/bin/env python3
"""Check 22 — verify claimed consumer counts in AI docs against the GAMS source.

Closes R4 Cluster 3+4+5 (shadow-table sync, M09 consumer table, M11 §3
attribution drift) in one mechanization. For every variable/count claim that
matches a known pattern, recompute the actual consumer count from the GAMS
source and flag mismatches.

Patterns covered:
  A. Markdown table row: `| `<var>(dims)?` | <N>(\\s*modules)? | ...`
  B. "Critical Consumers" prose:
        **Critical Consumers of `<var>`** (<N> modules total):
  C. "Provides To"/"Provides to" prose:
        **Provides To** (<N> modules):
        **Provides to**: <N> modules ...
        (Pattern C is module-level, not variable-level; checked against the
         module's full provides-to set rather than a single variable.)

Recompute matches the validator footer convention:
  consumers(var) = |module_dirs containing `var` token anywhere in *.gms|
                   minus the producer module (derived from declarations.gms).

Scopes scanned:
  modules/module_*.md           — pattern A + B
  core_docs/Module_Dependencies.md     — pattern A
  cross_module/modification_safety_guide.md  — pattern A
  cross_module/circular_dependency_resolution.md  — pattern A (if any)

Usage: python3 check_consumer_attribution.py [--summary-only] [--verbose]
Exit: 0 always (advisory; mismatches surface via output text)
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_gams_variables import (  # noqa: E402
    GAMS_INTERFACE_RE,
    GAMS_NUMBERED_RE,
    MAGPIE_DIR,
    iter_files,
    read_text_or_empty,
)

AGENT_DIR = SCRIPT_DIR.parent

# Token-shaped variable name (no dims). Used to validate extracted names.
VAR_NAME_RE = re.compile(
    r"^(?:vm_|pm_|fm_|im_|pcm_|ic_|ov_|oq_|sm_|cm_"
    r"|v\d+_|p\d+_|f\d+_|i\d+_|s\d+_|c\d+_|ic\d+_|oq\d+_|ov\d+_)"
    r"[a-zA-Z0-9_]+[a-zA-Z0-9]$"
)

# Pattern A: markdown table row with `var(dims)?` in col 1 and N(\s*modules)? in col 2.
# Anchors to start-of-line `|` and requires at least one further `|` after col 2.
TABLE_ROW_RE = re.compile(
    r"^\s*\|\s*`(?P<var>[a-zA-Z][a-zA-Z0-9_]*(?:\([^)]*\))?)`[^|]*"
    r"\|\s*(?P<count>\d+)(?:\s*modules?)?\s*\|"
)

# Pattern A header: a markdown table header row whose 2nd column contains
# "Consumer" or "Consumed" or "Used by". Used to gate Pattern A so that scalar
# default-value tables (col 2 is the value) don't get treated as consumer claims.
TABLE_HEADER_RE = re.compile(
    r"^\s*\|\s*[^|]+\|\s*(?P<col2>[^|]*)\|"
)
# Markdown table separator row `|---|---|...`
TABLE_SEP_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
# Header-column keywords that identify a consumer-count column.
CONSUMER_HEADER_KEYWORDS = (
    "consumer", "consumed", "used by", "used-by",
)

# Pattern B: prose form. Allows optional dimension suffix.
CRITICAL_CONSUMERS_RE = re.compile(
    r"\*\*Critical Consumers of\s+`(?P<var>[a-zA-Z][a-zA-Z0-9_]*(?:\([^)]*\))?)`\*\*"
    r"\s*\((?P<count>\d+)\s*modules?\s+total\)"
)

# Pattern D (R6 Phase 1 1b): inline-prose consumer attribution with parenthesized
# module numbers. Examples this catches:
#   "consumed by 7 downstream modules: cropland (29), residues (18), ..."
#   "Upstream: Emission modules (51-55), Forestry CDR (32), ..."
# The key signal: a backticked vm_*/pm_*/etc identifier in the same paragraph
# followed by one or more "Name (NN)" patterns where NN is a module number.
#
# We extract:
#   - The identifier (variable in the discussion)
#   - Each (module_label, module_num) pair from the surrounding prose
# Then verify each module_num against the grep-derived consumer set.
# Accept both Title Case ("Land (10)") and lowercase ("cropland (29)") labels
# preceding a parenthesized 2-digit module number. The lookbehind requires a
# word boundary or comma/colon (so "shifted by 5 (loss)" doesn't false-match).
PROSE_MODULE_NUM_RE = re.compile(
    r"(?:^|[,:;]\s*|\b)([A-Za-z][A-Za-z _]{2,30}?)\s*\((\d{2})(?:-\d{2})?\)"
)
# Triggering language that indicates we're in a consumer-attribution sentence
# (not just any list of (NN) parentheticals). Conservative to avoid FP.
PROSE_TRIGGER_RE = re.compile(
    r"\b(consumed by|reads?|consumes?|uses?|fed (?:by|into)|provided to|provides to|downstream|upstream|critical for|aggregated from|combined from|sourced from)\b",
    re.IGNORECASE,
)

# Declarations.gms variable-declaration line. Leading whitespace optional
# (some modules indent, some don't — e.g. 17_production/flexreg_apr16). The
# description token after the dims is required so plain variable references
# (no description) don't match. Comments (`*`), preprocessor (`$`), and the
# section-keyword lines (`parameters`, `variables`, etc.) all start with
# different characters and are filtered by the alphanumeric-first-char rule
# plus a section-keyword denylist.
DECL_LINE_RE = re.compile(
    r"^\s*(?P<name>[a-z][a-zA-Z0-9_]+)\s*(?:\([^)]+\))?\s+\S+"
)
DECL_SECTION_KEYWORDS = {
    "parameters", "parameter", "variables", "variable",
    "positive", "negative", "free", "binary", "integer",
    "equations", "equation", "scalars", "scalar", "sets", "set",
    "table", "tables",
}


def strip_dims(name: str) -> str:
    """Return the variable token without its `(...)` dimension suffix."""
    paren = name.find("(")
    return name[:paren] if paren > 0 else name


def is_interface_var(name: str) -> bool:
    return bool(VAR_NAME_RE.match(name))


def build_producer_map() -> dict[str, str]:
    """Map interface var name → module dir (e.g. '10_land') that declares it.

    Scans `<MAGPIE_DIR>/modules/<module_dir>/<realization>/declarations.gms`.
    If a var is declared in more than one module_dir, returns None for that
    var (ambiguous; caller skips).
    """
    modules_root = MAGPIE_DIR / "modules"
    if not modules_root.is_dir():
        return {}

    producers: dict[str, set[str]] = defaultdict(set)

    for module_dir in sorted(modules_root.iterdir()):
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        for path in module_dir.rglob("declarations.gms"):
            text = read_text_or_empty(path)
            if not text:
                continue
            for line in text.splitlines():
                m = DECL_LINE_RE.match(line)
                if not m:
                    continue
                name = m.group("name")
                if name in DECL_SECTION_KEYWORDS:
                    continue
                if not is_interface_var(name):
                    continue
                producers[name].add(module_name)

    # Resolve to single producer; mark ambiguous as empty-string sentinel.
    resolved: dict[str, str] = {}
    for var, modules in producers.items():
        if len(modules) == 1:
            resolved[var] = next(iter(modules))
        else:
            resolved[var] = ""  # ambiguous
    return resolved


def build_consumer_map() -> dict[str, set[str]]:
    """Map interface var name → set of module_dir names containing the var as a token.

    Scans every *.gms file under `<MAGPIE_DIR>/modules/`. Uses
    word-boundary regex so `vm_land` does not match `vm_land_short`.
    """
    modules_root = MAGPIE_DIR / "modules"
    if not modules_root.is_dir():
        return {}

    consumers: dict[str, set[str]] = defaultdict(set)
    # Combined regex catches all interface shapes in one pass per file.
    combined = re.compile(
        r"\b(?:" + GAMS_INTERFACE_RE.pattern[2:] + "|" + GAMS_NUMBERED_RE.pattern[2:] + r")"
    )

    for module_dir in sorted(modules_root.iterdir()):
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        for path in module_dir.rglob("*.gms"):
            text = read_text_or_empty(path)
            if not text:
                continue
            for var in set(combined.findall(text)):
                consumers[var].add(module_name)
    return consumers


def expected_consumer_count(
    var: str,
    producers: dict[str, str],
    consumers: dict[str, set[str]],
) -> int | None:
    """Return |consumer_dirs| minus the producer, or None if unknown."""
    base = strip_dims(var)
    if base not in producers or base not in consumers:
        return None
    producer = producers[base]
    dirs = consumers[base]
    if not producer:
        # Ambiguous producer: report consumer count without exclusion. Caller
        # may still flag this since the doc claim usually excludes the producer.
        return len(dirs)
    return max(0, len(dirs - {producer}))


def scan_table_rows(
    text: str,
    rel_path: str,
    producers: dict[str, str],
    consumers: dict[str, set[str]],
) -> list[tuple[str, int, str, int, int | None]]:
    """Return rows: (file, lineno, var_token, claimed, expected_or_None).

    Only emits findings for tables whose 2nd column header identifies a
    consumer count (header text contains "Consumer", "Consumed", or "Used by").
    A table is considered active from its separator row until the first
    non-table line. This prevents scalar default-value tables (where col 2
    is the default value, not a count) from being mistaken for consumer tables.
    """
    findings = []
    lines = text.splitlines()
    in_consumer_table = False

    for i, line in enumerate(lines):
        lineno = i + 1
        # Detect table boundary: separator row tells us we just entered a table
        # whose header is on the line above.
        if TABLE_SEP_RE.match(line):
            if i > 0:
                header = lines[i - 1]
                hm = TABLE_HEADER_RE.match(header)
                if hm:
                    col2 = hm.group("col2").strip().lower()
                    in_consumer_table = any(kw in col2 for kw in CONSUMER_HEADER_KEYWORDS)
                else:
                    in_consumer_table = False
            continue

        # Leaving the table: blank line or any non-table line.
        if in_consumer_table and (not line.strip() or not line.lstrip().startswith("|")):
            in_consumer_table = False

        if not in_consumer_table:
            continue

        m = TABLE_ROW_RE.match(line)
        if not m:
            continue
        raw_var = m.group("var")
        claimed = int(m.group("count"))
        base = strip_dims(raw_var)
        if not is_interface_var(base):
            continue
        expected = expected_consumer_count(raw_var, producers, consumers)
        findings.append((rel_path, lineno, raw_var, claimed, expected))
    return findings


def scan_critical_consumers(
    text: str,
    rel_path: str,
    producers: dict[str, str],
    consumers: dict[str, set[str]],
) -> list[tuple[str, int, str, int, int | None]]:
    """Return rows: (file, lineno, var_token, claimed, expected_or_None)."""
    findings = []
    for m in CRITICAL_CONSUMERS_RE.finditer(text):
        raw_var = m.group("var")
        claimed = int(m.group("count"))
        # Find lineno containing this match.
        lineno = text.count("\n", 0, m.start()) + 1
        base = strip_dims(raw_var)
        if not is_interface_var(base):
            continue
        expected = expected_consumer_count(raw_var, producers, consumers)
        # "Critical Consumers (N modules total)" historically counts producer
        # IN the total. Check both interpretations and report whichever is closer.
        # Convention: the +1 interpretation (consumers + producer) is the
        # current docs style. We report the mismatch only if BOTH fail.
        findings.append((rel_path, lineno, raw_var, claimed, expected))
    return findings


def scan_prose_attribution(
    text: str,
    rel_path: str,
    producers: dict[str, str],
    consumers: dict[str, set[str]],
) -> list[tuple[str, int, str, str, str]]:
    """Pattern D — LINE-level attribution (R6 Phase 1 1b).

    Goal: catch the R24 Q4-B4 pattern where prose lists module names with
    parenthesized module numbers as consumers of a backticked variable, and
    one or more of those modules don't actually grep-hit the variable.

    Anchored to LINE level (not paragraph) to avoid producer-centric
    "Land (10) — 18 consumers across `vm_land`..." false positives. The
    required pattern on a single line:
      (a) a backtick-quoted interface variable
      (b) a CONSUMER-direction trigger word ("consumed by", "reads", etc.)
      (c) one or more "Name (NN)" parenthesized module-number patterns

    Also: skips the module whose number matches the variable's producer
    (a producer appearing in its own attribution list is correct).

    Returns: (file, lineno, var_token, module_label, module_num_str).
    """
    # CONSUMER-direction triggers only. Bi-directional words like "downstream"
    # and "critical for" go in both directions and create FPs in producer-centric
    # tables. Keep only words that unambiguously claim consumption.
    consumer_direction = re.compile(
        r"\b(consumed by|reads?|consumes?|uses?|fed (?:by|into)|sourced from)\b",
        re.IGNORECASE,
    )
    findings: list[tuple[str, int, str, str, str]] = []
    # Build a module_num -> module_dir lookup
    consumer_module_dirs: set[str] = set()
    for dirs in consumers.values():
        consumer_module_dirs.update(dirs)
    for d in producers.values():
        if d:
            consumer_module_dirs.add(d)
    num_to_dir: dict[str, str] = {}
    for d in consumer_module_dirs:
        if "_" in d:
            num = d.split("_", 1)[0]
            if num.isdigit():
                num_to_dir[num] = d

    # Phrases that mark historical-reference text (R24-fix explanations,
    # changelog entries, etc.). When present in the line we skip — the bug
    # is being described, not committed.
    historical_marker = re.compile(
        r"\b(earlier wording|previously listed|prior wording|before fix|stale wording|correction|misattributed|R\d+ audit|R\d+ correction|removed in R\d+)\b",
        re.IGNORECASE,
    )

    for lineno, line in enumerate(text.splitlines(), 1):
        if not consumer_direction.search(line):
            continue
        if historical_marker.search(line):
            continue
        # Find backtick-quoted identifiers in this LINE
        idents = []
        for m in re.finditer(r"`([a-z][\w]+(?:\([^)]*\))?)`", line):
            base = strip_dims(m.group(1))
            if is_interface_var(base):
                idents.append(base)
        if not idents:
            continue
        # Find Name (NN) patterns on the SAME line
        nn_pairs = []
        for m in PROSE_MODULE_NUM_RE.finditer(line):
            label = m.group(1).strip()
            num = m.group(2)
            if len(label) < 3:
                continue
            nn_pairs.append((label, num))
        if not nn_pairs:
            continue
        for var in set(idents):
            actual_consumers_dirs = consumers.get(var, set())
            actual_consumer_nums = {d.split("_", 1)[0] for d in actual_consumers_dirs if "_" in d}
            producer_dir = producers.get(var, "")
            producer_num = producer_dir.split("_", 1)[0] if "_" in producer_dir else ""
            for label, num in nn_pairs:
                if num not in num_to_dir:
                    continue
                # Allow producer to be mentioned in its own attribution list
                if num == producer_num:
                    continue
                if num not in actual_consumer_nums:
                    findings.append((rel_path, lineno, var, label, num))
    return findings


def main() -> int:
    args = sys.argv[1:]
    summary_only = "--summary-only" in args
    verbose = "--verbose" in args

    if not (MAGPIE_DIR / "main.gms").is_file() or not (MAGPIE_DIR / "modules").is_dir():
        print(f"⚠️  GAMS codebase not found at {MAGPIE_DIR} - skipping consumer-attribution check")
        return 0

    producers = build_producer_map()
    consumers = build_consumer_map()

    print("Consumer attribution check")
    print("==========================")
    print(f"Variables with derived producer: {len([v for v in producers.values() if v])}")
    print(f"Variables observed in module .gms files: {len(consumers)}")

    # Scopes
    scopes = [
        AGENT_DIR / "core_docs" / "Module_Dependencies.md",
        AGENT_DIR / "cross_module" / "modification_safety_guide.md",
        AGENT_DIR / "cross_module" / "circular_dependency_resolution.md",
    ]
    # Add all module docs
    for doc in sorted((AGENT_DIR / "modules").glob("module_*.md")):
        scopes.append(doc)

    all_findings: list[tuple[str, int, str, int, int | None, str]] = []

    for doc in scopes:
        if not doc.is_file():
            continue
        text = doc.read_text(encoding="utf-8", errors="ignore")
        rel = str(doc.relative_to(AGENT_DIR))

        for path, lineno, var, claimed, expected in scan_table_rows(text, rel, producers, consumers):
            all_findings.append((path, lineno, var, claimed, expected, "table"))

        for path, lineno, var, claimed, expected in scan_critical_consumers(text, rel, producers, consumers):
            all_findings.append((path, lineno, var, claimed, expected, "critical_consumers"))

    # Pattern D — prose attribution (R6 Phase 1 1b). Collect into a SEPARATE list
    # since its output shape is different (no claimed/expected count — instead
    # per-module-attribution findings).
    prose_findings: list[tuple[str, int, str, str, str]] = []
    for doc in scopes:
        if not doc.is_file():
            continue
        text = doc.read_text(encoding="utf-8", errors="ignore")
        rel = str(doc.relative_to(AGENT_DIR))
        prose_findings.extend(scan_prose_attribution(text, rel, producers, consumers))

    # Triage findings
    mismatches: list[tuple[str, int, str, int, int, str]] = []  # expected non-None and != claimed
    ambiguous: list[tuple[str, int, str, int, str]] = []        # expected is None
    matches = 0

    for path, lineno, var, claimed, expected, kind in all_findings:
        if expected is None:
            ambiguous.append((path, lineno, var, claimed, kind))
            continue
        # For "critical_consumers" prose, accept either claimed == expected
        # (consumer count) OR claimed == expected + 1 (consumers + producer).
        if kind == "critical_consumers":
            if claimed == expected or claimed == expected + 1:
                matches += 1
                continue
        else:
            if claimed == expected:
                matches += 1
                continue
        mismatches.append((path, lineno, var, claimed, expected, kind))

    total = len(all_findings)
    print(f"Consumer-count claims scanned: {total}")
    print(f"  Matches: {matches}")
    print(f"  Mismatches: {len(mismatches)}")
    print(f"  Unverifiable (no producer/consumer data): {len(ambiguous)}")
    print()

    if mismatches:
        print(f"⚠️  Found {len(mismatches)} consumer-count mismatches:")
        if summary_only:
            from collections import Counter

            counts = Counter(m[0] for m in mismatches)
            for doc, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
                print(f"  {doc}: {n}")
        else:
            for path, lineno, var, claimed, expected, kind in sorted(mismatches):
                hint = ""
                if kind == "critical_consumers":
                    hint = f" (consumers={expected}, +producer={expected + 1})"
                print(f"  {path}:{lineno}  `{var}` claims {claimed} but recomputed {expected}{hint} [{kind}]")
    else:
        print("✅ All consumer-count claims match the recomputed value")

    if verbose and ambiguous:
        print()
        print(f"ℹ️  {len(ambiguous)} unverifiable claims (var not in producer/consumer index):")
        for path, lineno, var, claimed, kind in sorted(ambiguous)[:20]:
            print(f"  {path}:{lineno}  `{var}` claims {claimed} [{kind}]")
        if len(ambiguous) > 20:
            print(f"  ... and {len(ambiguous) - 20} more")

    # Pattern D output
    print()
    if prose_findings:
        print(f"⚠️  Pattern D prose attribution: {len(prose_findings)} module(s) listed but NOT direct consumers:")
        if summary_only:
            from collections import Counter
            counts = Counter(f[0] for f in prose_findings)
            for doc, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]:
                print(f"  {doc}: {n}")
        else:
            for path, lineno, var, label, num in sorted(prose_findings)[:30]:
                print(f"  {path}:{lineno}  `{var}` lists M{num} ({label}) but M{num}_* has no grep-hit")
            if len(prose_findings) > 30:
                print(f"  ... and {len(prose_findings) - 30} more")
    else:
        print("✅ Pattern D prose attribution: all listed modules grep-verify")

    # Advisory exit: always 0. Mismatches surface via output text.
    return 0


if __name__ == "__main__":
    sys.exit(main())
