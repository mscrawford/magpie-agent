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

import json
import os
import re
import subprocess
import sys
import tempfile
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
# Pattern D-extended (R25 Phase 1 follow-up): also recognize `Module N` /
# `Module N (Description)` / `Module's q*_*` forms used pervasively in
# module_38.md and similar producer-side docs. The R25 Q4 finding showed
# the original "Name (NN)" pattern missed entirely when the doc wrote
# `consumed by Module 11 via q11_cost_reg`. Capture just the 2-digit module
# number; the label is implicitly "Module".
PROSE_MODULE_BARE_RE = re.compile(
    r"\bModule\s+(\d{2})\b",
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
        # Find module-number references on the SAME line:
        #   - "Name (NN)" form (Pattern D original) — keep label
        #   - "Module N" bare form (Pattern D extended for R25 Q4 class)
        # Both forms feed the same nn_pairs list so positive-evidence and
        # negative-evidence (Pattern D2) checks see a unified listed set.
        nn_pairs = []
        seen_nums = set()
        for m in PROSE_MODULE_NUM_RE.finditer(line):
            label = m.group(1).strip()
            num = m.group(2)
            if len(label) < 3:
                continue
            if num in seen_nums:
                continue
            seen_nums.add(num)
            nn_pairs.append((label, num))
        for m in PROSE_MODULE_BARE_RE.finditer(line):
            num = m.group(1)
            if num in seen_nums:
                continue
            seen_nums.add(num)
            nn_pairs.append(("Module", num))
        if not nn_pairs:
            continue
        for var in set(idents):
            actual_consumers_dirs = consumers.get(var, set())
            actual_consumer_nums = {d.split("_", 1)[0] for d in actual_consumers_dirs if "_" in d}
            producer_dir = producers.get(var, "")
            producer_num = producer_dir.split("_", 1)[0] if "_" in producer_dir else ""
            listed_nums = {num for _, num in nn_pairs}
            for label, num in nn_pairs:
                if num not in num_to_dir:
                    continue
                # Allow producer to be mentioned in its own attribution list
                if num == producer_num:
                    continue
                if num not in actual_consumer_nums:
                    findings.append((rel_path, lineno, var, label, num))
    return findings


def scan_prose_omissions(
    text: str,
    rel_path: str,
    producers: dict[str, str],
    consumers: dict[str, set[str]],
) -> list[tuple[str, int, str, str, str, str]]:
    """Pattern D2 — NEGATIVE-evidence (R25 Phase 1 follow-up).

    Goal: catch the R25 Q4-B1 pattern where a producer-side doc enumerates
    consumers but OMITS a real consumer. Pre-R25, Pattern D's positive-
    evidence check verified that listed modules grep-match, but never asked
    the inverse: "are there modules that grep-match but are absent from
    the listed set?"

    Triggers a finding when:
      (a) line has a backticked interface variable, AND
      (b) line has a consumer-direction trigger word, AND
      (c) line names one or more modules (via "Module N" or "Name (NN)"), AND
      (d) actual_consumer_nums - listed_nums - {producer_num} is NON-EMPTY

    Conservative guard: skip lines containing partial-list hedges
    ("primary", "main", "most important", "key", "e.g.", "such as", "etc")
    — these signal the doc is intentionally not enumerating all consumers.

    Returns: (file, lineno, var, omitted_module_num, omitted_module_label, omitted_module_dir).
    """
    # Consumer-direction trigger. Tightened (R25 follow-up) to exclude
    # hyphen-compound noun forms — `\buse\b` would otherwise match "use"
    # inside "land-use", "water-use", "end-use", which is a common pattern
    # in MAgPIE docs that has nothing to do with consumer attribution.
    consumer_direction = re.compile(
        r"\b(?:consumed by|reads?|consumes?|fed (?:by|into)|sourced from"
        r"|(?<!-)uses?(?!-))\b",
        re.IGNORECASE,
    )
    historical_marker = re.compile(
        r"\b(earlier wording|previously listed|prior wording|before fix|stale wording|correction|misattributed|R\d+ audit|R\d+ correction|removed in R\d+)\b",
        re.IGNORECASE,
    )
    # Hedges that signal the doc is intentionally listing a subset, not all
    # consumers. If present, skip the line — the omission is by design.
    partial_list_hedge = re.compile(
        r"\b(primary|main|most important|key consumer|principal|e\.?g\.|such as|etc\b|among others|including but not limited to"
        r"|may be affected|broader|wider|touched by|set of)\b",
        re.IGNORECASE,
    )

    findings: list[tuple[str, int, str, str, str, str]] = []
    # num -> dir mapping (built same way as scan_prose_attribution)
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

    # Helper: extract listed module numbers from a line (both regex forms)
    def line_listed_nums(line: str) -> set[str]:
        nums: set[str] = set()
        for m in PROSE_MODULE_NUM_RE.finditer(line):
            label = m.group(1).strip()
            if len(label) >= 3:
                nums.add(m.group(2))
        for m in PROSE_MODULE_BARE_RE.finditer(line):
            nums.add(m.group(1))
        return nums

    # Helper: extract backticked interface var bases from a line
    def line_idents(line: str) -> list[str]:
        out = []
        for m in re.finditer(r"`([a-z][\w]+(?:\([^)]*\))?)`", line):
            base = strip_dims(m.group(1))
            if is_interface_var(base):
                out.append(base)
        return out

    # Helper: bullet-list prefix (whitespace + `-` or `*` followed by space)
    bullet_prefix_re = re.compile(r"^(\s*[-*]\s+)")

    # If this doc is a per-module doc (modules/module_NN.md), the doc's own
    # module is implicitly the "subject" — readers don't expect it to list
    # itself as a consumer. Excluding it from omission candidates eliminates
    # the structural FP class where a producer-side description happens to
    # appear in the consumer's own doc.
    mod_m = re.search(r"module_(\d{2})", rel_path)
    current_doc_num = mod_m.group(1) if mod_m else None

    lines = text.splitlines()
    for lineno, line in enumerate(lines, 1):
        if not consumer_direction.search(line):
            continue
        if historical_marker.search(line):
            continue
        if partial_list_hedge.search(line):
            continue
        idents = line_idents(line)
        if not idents:
            continue
        listed_nums = line_listed_nums(line)
        if not listed_nums:
            continue

        # BULLET-LIST AGGREGATION (R25 Phase 1 follow-up):
        # If this line is a bullet item AND adjacent bullet items at the same
        # indent level reference the same variable, combine their listed_nums.
        # Without this, an enumeration like
        #     - Module 11 (Costs) — `vm_X` ...
        #     - Module 36 (Employment) — `vm_X` ...
        # produces a false "omits M11" flag on the M36 bullet (and vice versa
        # if we scanned forward only). Walk both directions until the bullet
        # chain breaks (different indent, different prefix, blank line gap >1,
        # or var not mentioned).
        m_bullet = bullet_prefix_re.match(line)
        if m_bullet:
            indent_prefix = m_bullet.group(1)
            # Walk back
            for j in range(lineno - 2, max(-1, lineno - 10), -1):
                if j < 0 or j >= len(lines):
                    break
                prev = lines[j]
                if not prev.strip():
                    # Allow ONE blank line gap, then stop
                    if j > 0 and not lines[j - 1].strip():
                        break
                    continue
                if not prev.startswith(indent_prefix):
                    break
                # Same indent bullet; check if it mentions any of our idents
                prev_idents = set(line_idents(prev))
                if not (prev_idents & set(idents)):
                    break
                listed_nums |= line_listed_nums(prev)
            # Walk forward
            for j in range(lineno, min(len(lines), lineno + 10)):
                if j >= len(lines):
                    break
                nxt = lines[j]
                if not nxt.strip():
                    if j + 1 < len(lines) and not lines[j + 1].strip():
                        break
                    continue
                if not nxt.startswith(indent_prefix):
                    break
                nxt_idents = set(line_idents(nxt))
                if not (nxt_idents & set(idents)):
                    break
                listed_nums |= line_listed_nums(nxt)

        for var in set(idents):
            actual_consumers_dirs = consumers.get(var, set())
            actual_consumer_nums = {d.split("_", 1)[0] for d in actual_consumers_dirs if "_" in d}
            producer_dir = producers.get(var, "")
            producer_num = producer_dir.split("_", 1)[0] if "_" in producer_dir else ""
            # Exclude: (a) producer module (already its own attribution if
            # mentioned), (b) the CURRENT DOC's module (self-reference; the
            # doc is about this module and wouldn't list itself).
            exclude_nums: set[str] = set()
            if producer_num:
                exclude_nums.add(producer_num)
            if current_doc_num:
                exclude_nums.add(current_doc_num)
            omitted = actual_consumer_nums - listed_nums - exclude_nums
            for num in sorted(omitted):
                if num not in num_to_dir:
                    continue
                module_dir = num_to_dir[num]
                # Module label: take the dir name minus the leading number
                label = module_dir.split("_", 1)[1] if "_" in module_dir else module_dir
                findings.append((rel_path, lineno, var, num, label, module_dir))
    return findings


# Pattern D3 (2026-05-29): MULTI-LINE producer/populator attribution. Pattern D is
# line-anchored and consumer-direction, so it misses the G2 class where a populator
# claim ("... populate `vm_carbon_stock`") has its module-number list on PRECEDING
# bullet/prose lines. POPULATOR_VERB_RE is the producer-direction trigger set Pattern D
# lacks ("populate" was the exact verb in the G2 doc bug).
# Narrowed to 'populate' (the producer-direction verb in the actual G2 doc bug).
# 'provide/compute/calculate/contribute' are too generic - they appear in
# consumer-direction and unrelated prose and produced ~30 corpus false positives in
# testing (e.g. vm_dem_food "provides", pm_interest). 'populate(s|d)', with the variable
# as its object, is specific to producer attribution and is what the G2 doc bug used.
POPULATOR_VERB_RE = re.compile(r"\b(populates?|populated)\b", re.IGNORECASE)
_BACKTICK_SPAN_RE = re.compile(r"`([^`]+)`")
_ID_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_]+")
_POPULATOR_HISTORICAL_RE = re.compile(
    r"\b(earlier wording|previously listed|prior wording|before fix|stale wording|"
    r"correction|misattributed|R\d+ audit|R\d+ correction|removed in R\d+|"
    r"does not populate|not a populator|separate)\b",
    re.IGNORECASE,
)


def _backticked_interface_vars(line: str) -> set[str]:
    out: set[str] = set()
    for span in _BACKTICK_SPAN_RE.findall(line):
        for tok in _ID_TOKEN_RE.findall(span):
            base = strip_dims(tok)
            if is_interface_var(base):
                out.add(base)
    return out


def scan_populator_claims(
    text: str,
    rel_path: str,
    producers: dict[str, str],
    consumers: dict[str, set[str]],
    window: int = 8,
) -> list[tuple[str, int, str, str, str]]:
    """Pattern D3 — multi-line producer/populator attribution (G2 class).

    On a line carrying a populator verb AND a backticked interface var, scan a tight
    backward window (stops at a heading or a 2+ blank-line gap) for `Module NN` /
    `Name (NN)` numbers. Require >= 2 module numbers (a list, where G2 lived) to
    reduce single-stray-number FPs. Flag any listed module that does NOT reference
    the variable in any *.gms (phantom populator - the G2 M58-peatland error). Skips
    the producer and historical-correction text. Advisory.

    Returns (file, lineno, var, module_num, module_label).
    """
    findings: list[tuple[str, int, str, str, str]] = []
    lines = text.splitlines()
    num_to_dir: dict[str, str] = {}
    seen: set[str] = set()
    for dirs in consumers.values():
        seen.update(dirs)
    for d in producers.values():
        if d:
            seen.add(d)
    for d in seen:
        if "_" in d and d.split("_", 1)[0].isdigit():
            num_to_dir[d.split("_", 1)[0]] = d

    for i, line in enumerate(lines):
        if not POPULATOR_VERB_RE.search(line) or _POPULATOR_HISTORICAL_RE.search(line):
            continue
        vars_here = {v for v in _backticked_interface_vars(line) if v in consumers}
        if not vars_here:
            continue
        # backward window: collect module numbers, stop at heading / 2+ blank gap
        win = [(i + 1, line)]
        blanks = 0
        for j in range(i - 1, max(-1, i - 1 - window), -1):
            lj = lines[j]
            if lj.strip().startswith("#"):
                break
            if not lj.strip():
                blanks += 1
                if blanks >= 2:
                    break
                continue
            blanks = 0
            win.append((j + 1, lj))
        nums: dict[str, int] = {}
        for ln_no, lj in win:
            if _POPULATOR_HISTORICAL_RE.search(lj):
                continue
            for m in PROSE_MODULE_BARE_RE.finditer(lj):
                nums.setdefault(m.group(1), ln_no)
            for m in PROSE_MODULE_NUM_RE.finditer(lj):
                nums.setdefault(m.group(2), ln_no)
        if len(nums) < 2:  # require a list; single strays are too FP-prone
            continue
        for var in sorted(vars_here):
            producer_dir = producers.get(var) or ""
            for num, src_ln in sorted(nums.items()):
                d = num_to_dir.get(num)
                if not d or d == producer_dir:
                    continue
                if d not in consumers.get(var, set()):
                    label = d.split("_", 1)[1] if "_" in d else d
                    findings.append((rel_path, src_ln, var, num, label))
    return findings


def _write_selftest_fixture(root: Path) -> None:
    """Write a synthetic MAgPIE module tree exercising the REAL extractors.

    Deliberately covers the ground-truth branches the old self-test could not
    reach, because it hand-wrote the maps instead of building them:
      - single-module declaration  -> resolved producer
      - two-module declaration     -> "" ambiguous sentinel
      - section keywords / non-interface names -> skipped
      - token word-boundary        -> vm_land_short must NOT credit vm_land
    """
    def w(rel: str, text: str) -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    # MAGPIE_DIR sanity anchors that main() checks for.
    w("main.gms", "* synthetic\n")

    # 10_land declares vm_land (single producer) + vm_ambig (also in 32).
    w("modules/10_land/landmatrix_dec18/declarations.gms",
      "variables\n"
      " vm_land(j,land) land area\n"
      " vm_ambig(j) ambiguous on purpose\n"
      "positive variables\n"
      " v10_local(j) numbered-local, not a cross-module iface\n")

    # 32_forestry ALSO declares vm_ambig -> must resolve to "" (ambiguous).
    w("modules/32_forestry/dynamic_may24/declarations.gms",
      "variables\n"
      " vm_ambig(j) declared twice across modules\n")

    # 29_cropland CONSUMES vm_land in an equation.
    w("modules/29_cropland/detail_apr24/equations.gms",
      " q29_x(j) .. sum(land, vm_land(j,land)) =e= 1;\n")

    # 31_past mentions ONLY vm_land_short -> word boundary means it must NOT
    # be credited as a vm_land consumer. This is the substring-false-positive
    # class that has bitten real consumer attribution before.
    w("modules/31_past/default/equations.gms",
      " q31_y(j) .. vm_land_short(j) =e= 2;\n")

    # 52_carbon reads vm_land at SOLUTION level only (.l) -- a paren-only grep
    # would miss this; the extractor's token regex should still catch it.
    w("modules/52_carbon/normal_dec17/presolve.gms",
      " p52_tmp(j) = vm_land.l(j);\n")


def _scan_only() -> int:
    """Internal: drive the REAL extractors over MAGPIE_DIR and emit JSON.

    Exists so the self-test can exercise build_producer_map/build_consumer_map
    against a real tree on disk (via a MAGPIE_DIR-overridden subprocess) instead
    of stubbing them. Stubbing the ground-truth extractor is exactly the defect
    R57/W0a found across the battery; this must not reproduce it.
    """
    producers = build_producer_map()
    consumers = build_consumer_map()
    print(json.dumps({
        "producers": producers,
        "consumers": {k: sorted(v) for k, v in consumers.items()},
    }))
    return 0


def _self_test() -> int:
    """Positive control for Pattern D3.

    Two halves, deliberately:
      1. the DIFFING half (scan_populator_claims) against synthetic maps;
      2. the GROUND-TRUTH half (build_producer_map / build_consumer_map) driven
         for real over a synthetic tree on disk. Before R58 the extractors were
         100% dead to this test -- both could be replaced with `raise` and it
         still printed SELFTEST_OK.
    """
    failures = []
    producers = {"vm_carbon_stock": "56_ghg_policy"}
    consumers = {
        "vm_carbon_stock": {"29_cropland", "31_past", "32_forestry", "34_urban",
                            "35_natveg", "59_som", "52_carbon", "56_ghg_policy"},
        "vm_carbon_stock_croparea": {"30_croparea", "29_cropland"},
        "vm_peat": {"58_peatland"},
    }
    buggy = (
        "- **Module 30 (Crop):** Cropland carbon\n"
        "- **Module 31 (Pasture):** Pasture carbon\n"
        "- **Module 58 (Peatland):** Peatland carbon\n"
        "\n"
        "All populate `vm_carbon_stock` interface variable.\n"
    )
    nums = {h[3] for h in scan_populator_claims(buggy, "module_56.md", producers, consumers)}
    if "58" not in nums:
        failures.append(f"did not flag phantom M58 populator (got {sorted(nums)})")
    if "30" not in nums:
        failures.append(f"did not flag M30 (populates vm_carbon_stock_croparea, not vm_carbon_stock) (got {sorted(nums)})")
    if "31" in nums:
        failures.append("wrongly flagged M31 (a real populator)")
    good = (
        "- **Module 29 (Cropland):** crop carbon\n"
        "- **Module 31 (Pasture):** pasture carbon\n"
        "\n"
        "All populate `vm_carbon_stock`.\n"
    )
    if scan_populator_claims(good, "x.md", producers, consumers):
        failures.append("flagged a correct populator list (false positive)")

    # ---- expected_consumer_count: the count arithmetic ----------------------
    # Every finding this checker emits compares a doc's claimed number against
    # THIS function's return value, so a silent shift here mis-scores the whole
    # corpus while the battery stays green. Cases below pin: producer exclusion,
    # dim-stripping before lookup, the ambiguous-producer ("" sentinel) branch,
    # and the unknown-var guard -- including that the guard is a DISJUNCTION
    # (weakened to `and`, the orphan case indexes a missing key and crashes).
    ec_prod = {"vm_known": "10_land", "vm_ambig2": ""}
    ec_cons = {
        "vm_known": {"10_land", "29_cropland", "31_past"},
        "vm_ambig2": {"32_forestry", "35_natveg"},
        "vm_orphan": {"52_carbon"},  # in consumers, ABSENT from producers
    }
    got = expected_consumer_count("vm_known", ec_prod, ec_cons)
    if got != 2:
        failures.append(f"expected_consumer_count(vm_known) = {got}, want 2 (3 dirs minus producer)")
    got = expected_consumer_count("vm_known(j,land)", ec_prod, ec_cons)
    if got != 2:
        failures.append(f"expected_consumer_count: dims not stripped before lookup (got {got}, want 2)")
    got = expected_consumer_count("vm_ambig2", ec_prod, ec_cons)
    if got != 2:
        failures.append(f"expected_consumer_count(vm_ambig2) = {got}, want 2 (ambiguous -> no exclusion)")
    if expected_consumer_count("vm_orphan", ec_prod, ec_cons) is not None:
        failures.append("expected_consumer_count: var absent from producers must give None")
    if expected_consumer_count("vm_nowhere", ec_prod, ec_cons) is not None:
        failures.append("expected_consumer_count: var absent from both maps must give None")

    # ---- scan_table_rows: the table state machine --------------------------
    # Pattern A only counts rows inside a table whose 2nd column header says
    # "Consumers". Everything protecting that scope was untested: the initial
    # state, the separator/header handshake, and the exit condition. Each case
    # below is a state-machine transition, with negatives so a weakened guard
    # has somewhere to show up as a FALSE POSITIVE rather than a silent miss.
    tr_header = "| Variable | Consumers | Note |\n|---|---|---|\n"
    tr_cases = [
        # (label, text, expected [(lineno, var, claimed, expected_count)])
        ("consumer table scanned",
         tr_header + "| `vm_known` | 3 | ok |\n",
         [(3, "vm_known", 3, 2)]),
        # col2 is a default VALUE, not a consumer count -> table is out of scope.
        ("non-consumer header ignored",
         "| Scalar | Default | Note |\n|---|---|---|\n| `vm_known` | 3 | ok |\n",
         []),
        # Separator whose preceding line is not a table header at all.
        ("unparseable header ignored",
         "Some prose heading\n|---|---|---|\n| `vm_known` | 3 | ok |\n",
         []),
        # A row with no table above it must not inherit an active state.
        ("bare row before any table ignored",
         "| `vm_known` | 3 | ok |\n",
         []),
        # Prose ends the table; the later row must NOT still be counted.
        ("table exits on a prose line",
         tr_header + "| `vm_known` | 3 | ok |\n"
         "Prose interrupts the table here.\n"
         "| `vm_ambig2` | 9 | must not be scanned |\n",
         [(3, "vm_known", 3, 2)]),
        # Blank line ends the table too (the other arm of the exit disjunction).
        ("table exits on a blank line",
         tr_header + "| `vm_known` | 3 | ok |\n"
         "\n"
         "| `vm_ambig2` | 9 | must not be scanned |\n",
         [(3, "vm_known", 3, 2)]),
        # col1 is not an interface identifier -> not a variable claim.
        ("non-interface identifier ignored",
         tr_header + "| `foo_bar` | 3 | not an interface var |\n",
         []),
    ]
    for label, text, want in tr_cases:
        got = [(ln, var, claimed, exp)
               for _f, ln, var, claimed, exp in scan_table_rows(text, "t.md", ec_prod, ec_cons)]
        if got != want:
            failures.append(f"scan_table_rows [{label}]: got {got}, want {want}")

    # ---- GROUND-TRUTH half: drive the REAL extractors over a real tree -------
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write_selftest_fixture(root)
        env = dict(os.environ, MAGPIE_DIR=str(root))
        p = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--_scan-only"],
            capture_output=True, text=True, env=env, timeout=120,
        )
        if p.returncode != 0:
            failures.append(f"extractor subprocess rc={p.returncode}: {p.stderr[:300]}")
        else:
            data = json.loads(p.stdout)
            prod = data["producers"]
            cons = {k: set(v) for k, v in data["consumers"].items()}

            # build_producer_map
            if prod.get("vm_land") != "10_land":
                failures.append(f"build_producer_map: vm_land -> {prod.get('vm_land')!r}, want '10_land'")
            if prod.get("vm_ambig") != "":
                failures.append(f"build_producer_map: vm_ambig -> {prod.get('vm_ambig')!r}, want '' (ambiguous sentinel)")
            if "variables" in prod or "positive" in prod:
                failures.append("build_producer_map: leaked a GAMS section keyword into the map")
            # v10_local IS expected in the map: VAR_NAME_RE's alternation includes
            # `v\d+_`, so this checker's notion of "interface var" deliberately
            # spans module-numbered locals (it validates those too). Asserted so
            # a future narrowing of VAR_NAME_RE cannot silently drop them.
            if prod.get("v10_local") != "10_land":
                failures.append(f"build_producer_map: v10_local -> {prod.get('v10_local')!r}, want '10_land' (numbered locals are in scope by VAR_NAME_RE)")

            # build_consumer_map
            if "29_cropland" not in cons.get("vm_land", set()):
                failures.append(f"build_consumer_map: 29_cropland missing from vm_land consumers (got {sorted(cons.get('vm_land', []))})")
            if "31_past" in cons.get("vm_land", set()):
                failures.append("build_consumer_map: vm_land_short wrongly credited 31_past as a vm_land consumer (word-boundary broken)")
            if "vm_land_short" not in cons:
                failures.append("build_consumer_map: did not extract vm_land_short at all (fixture/regex mismatch)")
            if "52_carbon" not in cons.get("vm_land", set()):
                failures.append("build_consumer_map: missed a solution-level (.l) read in 52_carbon")

    if failures:
        print("SELF-TEST FAILED:", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        return 1
    print("SELF-TEST OK - Pattern D3 flags phantom/wrong populators across lines; "
          "clean lists pass.", file=sys.stderr)
    return 0


def main() -> int:
    args = sys.argv[1:]
    summary_only = "--summary-only" in args
    verbose = "--verbose" in args

    if "--_scan-only" in args:
        return _scan_only()

    if "--self-test" in args:
        rc = _self_test()
        if rc == 0:
            print("SELFTEST_OK check_consumer_attribution")
        return rc

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
    # Pattern D2 — prose omissions (R25 Phase 1 follow-up). Negative-evidence:
    # producer-side doc lists consumers but omits a real consumer.
    omission_findings: list[tuple[str, int, str, str, str, str]] = []
    populator_findings: list[tuple[str, int, str, str, str]] = []
    for doc in scopes:
        if not doc.is_file():
            continue
        text = doc.read_text(encoding="utf-8", errors="ignore")
        rel = str(doc.relative_to(AGENT_DIR))
        prose_findings.extend(scan_prose_attribution(text, rel, producers, consumers))
        omission_findings.extend(scan_prose_omissions(text, rel, producers, consumers))
        populator_findings.extend(scan_populator_claims(text, rel, producers, consumers))

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

    # Pattern D2 output (R25 Phase 1 follow-up): negative-evidence omissions.
    # Advisory — many "consumer" lines intentionally list a subset; we filter
    # out the partial-list hedges already, but residual FPs are expected.
    # Triage rule: if a doc consistently omits the same consumer across multiple
    # lines for the same variable, that's a real Pattern D2 doc bug.
    print()
    if omission_findings:
        print(f"ℹ️  Pattern D2 omission check: {len(omission_findings)} possibly-omitted consumer(s) (advisory):")
        if summary_only:
            from collections import Counter
            # Aggregate by (file, var, omitted_num) to surface repeated omissions
            counts = Counter((f[0], f[2], f[3]) for f in omission_findings)
            top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
            for (doc, var, num), n in top:
                print(f"  {doc}  `{var}` omits M{num} ({n} line{'s' if n > 1 else ''})")
        else:
            for path, lineno, var, num, label, module_dir in sorted(omission_findings)[:30]:
                print(f"  {path}:{lineno}  `{var}` mentions consumers but omits M{num} ({label}) — grep-hits in module {module_dir}")
            if len(omission_findings) > 30:
                print(f"  ... and {len(omission_findings) - 30} more")
    else:
        print("✅ Pattern D2 omission check: no obvious consumer omissions detected")

    # Pattern D3 output (2026-05-29): multi-line producer/populator attribution.
    print()
    if populator_findings:
        uniq = sorted(set(populator_findings))
        print(f"⚠️  Pattern D3 populator attribution: {len(uniq)} listed populator(s) with NO grep-hit on the variable:")
        if summary_only:
            from collections import Counter
            counts = Counter((f[0], f[2], f[3]) for f in uniq)
            for (doc, var, num), n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:15]:
                print(f"  {doc}  `{var}` lists M{num} as populator ({n} line{'s' if n > 1 else ''})")
        else:
            for path, lineno, var, num, label in uniq[:30]:
                print(f"  {path}:{lineno}  `{var}` lists M{num} ({label}) as a populator but M{num}_* has no grep-hit")
            if len(uniq) > 30:
                print(f"  ... and {len(uniq) - 30} more")
    else:
        print("✅ Pattern D3 populator attribution: no phantom populators detected")

    # Advisory exit: always 0. Mismatches surface via output text.
    return 0


if __name__ == "__main__":
    sys.exit(main())
