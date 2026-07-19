#!/usr/bin/env python3
"""check_attribution_tables.py — advisory Check: interface-attribution TABLES vs code.

The COMPLEMENT to check_role_attribution.py (Check 31). Check 31 mechanizes the
DECLARED half of MANDATE 18 from PROSE ("Module X provides `var`", "Declared in: NN").
It does NOT parse the "Provides To (Outputs)" / "Receives From (Inputs)" markdown
TABLES in module_XX.md — which is exactly where every R54 Critical lived (e.g.
module_32.md attributed 4 forestry interfaces to Module 10 when their sole consumer
is Module 58). Those tables survived ~50 rounds because the LLM auditor's per-instance
false-negative rate on cross-module attribution is high (FNR-limited, not
coverage-limited). This check is the deterministic, ~0-FNR complement.

WHAT IT DOES
  In every modules/module_XX.md, find the "Provides To" / "Receives From" tables and,
  for each row, read col-1 (the claimed related module(s), `**NN_name**`) and col-2
  (the interface var(s)). For each claimed module M on a row, if M references NONE of
  that row's interface vars ANYWHERE in its GAMS code (declares / populates / reads —
  build_consumer_map is a `\\b`-anchored "referenced anywhere" set, so `.l`/`.lo`
  attribute reads are included and there is no both-endpoints FN), the row's
  M<->var attribution is a PHANTOM -> flag.

DESIGN
  - PRECISION over recall (like Check 29/31): a module is flagged only if it references
    NONE of a row's vars. Multi-var rows ("A / B") and multi-module cells
    ("**52_carbon** / **56_ghg_policy**") are handled so a module that reads at least
    one of the row's vars is never flagged. OMISSIONS (a real consumer missing from the
    table) are deliberately NOT flagged here — build_consumer_map over-lists (includes
    the declarer + comment mentions), so omission-flagging is noisy; phantom is the
    primary, high-signal direction (the R54 Critical class).
  - Ground truth is the LOCAL parent checkout scanned by build_consumer_map
    (<MAGPIE_DIR>/modules). For an authoritative run point MAGPIE_DIR at a develop
    worktree; the working tree can lag (see memory magpie_agent_sync_against_develop).
  - Advisory only: main() always returns 0. --self-test returns 0/1 and is a hermetic
    positive+negative control (injected ref-map, no dependence on the parent repo).

Usage: python3 check_attribution_tables.py [--self-test]
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_consumer_attribution import (  # noqa: E402
    build_consumer_map,
    is_interface_var,
    strip_dims,
)

AGENT_DIR = SCRIPT_DIR.parent
DOCS_DIR = AGENT_DIR / "modules"
ALLOWLIST_PATH = AGENT_DIR / "audit" / "advisory_allowlist.json"
CHECK_NAME = "check_attribution_tables"

# Section headers that introduce an attribution table. Matched case-insensitively on a
# markdown header/bold line. "Provides To" = col-1 modules CONSUME the var; "Receives
# From" = col-1 modules PRODUCE it. Either way the membership test is identical: does the
# claimed module reference the var at all?
SECTION_RE = re.compile(r"^\s{0,3}(?:#{1,6}|\*\*|-)?\s*.*?(provides\s+to|receives\s+from)\b",
                        re.IGNORECASE)
# A markdown table row: leading '|' and at least two more '|'.
ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
SEP_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
# Module number inside col-1: `**10_land**`, `10_land`, or "Module 10" / "M10".
MODNUM_RE = re.compile(r"\b(\d{1,2})_[a-z]", re.IGNORECASE)
MODNUM_WORD_RE = re.compile(r"\b(?:module|m)\s*(\d{1,2})\b", re.IGNORECASE)
# House convention the other two patterns could not read: a col-1 label of the
# form `**70** (Livestock)` / `**09** (Drivers)` -- a BARE module number with no
# "Module"/"M" prefix and no NN_name form. Found 2026-07-19: this single gap was
# suppressing 52 rows across 4 docs (module_11/51/55/57), i.e. more coverage than
# the entire P0 LLM regularization pilot produced, at zero risk.
#
# Precision guards (cf. [[header_gated_markdown_tables]] -- row format alone is
# ambiguous across table types):
#   1. row scanning is ALREADY gated on the section heading (SECTION_RE), so a
#      bare number only counts inside a Provides-To / Receives-From section;
#   2. the number must be at cell START and be FOLLOWED BY A PARENTHESISED NAME,
#      which is what makes it a module label rather than a count, year, or index.
#      "2020 (baseline)" does not match: \d{1,2} takes "20", then a paren is
#      required immediately and "20 " intervenes.
MODNUM_LABEL_RE = re.compile(r"^\W*(\d{1,2})\W*\(")
# Interface-var token in col-2 (base prefixes; dims/slices stripped downstream).
VARTOK_RE = re.compile(r"\b((?:vm|pm|pcm|fm|sm|im|v|p|s|i|f|q)\d*_[a-z][a-zA-Z0-9_]*)")
# Header row whose col-1 is a label, not a module.
HEADER_CELL_RE = re.compile(r"^\s*\*{0,2}(module|source|target|consumer|producer|variable"
                            r"|interface|receives|provides|from|to)\b", re.IGNORECASE)


def load_allowlist() -> set[tuple[str, str]]:
    if not ALLOWLIST_PATH.exists():
        return set()
    try:
        data = json.loads(ALLOWLIST_PATH.read_text())
    except (ValueError, OSError):
        return set()
    out: set[tuple[str, str]] = set()
    rows = data if isinstance(data, list) else (data.get("allowlist") or data.get("entries") or [])
    for entry in rows:
        if entry.get("check") == CHECK_NAME:
            out.add((entry.get("file", ""), entry.get("key", "")))
    return out


def _mods_in_cell(cell: str) -> list[int]:
    nums = {int(m.group(1)) for m in MODNUM_RE.finditer(cell)}
    nums |= {int(m.group(1)) for m in MODNUM_WORD_RE.finditer(cell)}
    nums |= {int(m.group(1)) for m in MODNUM_LABEL_RE.finditer(cell)}
    return sorted(nums)


def _vars_in_cell(cell: str) -> list[str]:
    out: list[str] = []
    for m in VARTOK_RE.finditer(cell):
        base = strip_dims(m.group(1))
        if is_interface_var(base) and base not in out:
            out.append(base)
    return out


def scan_doc(text: str, rel_path: str, ref_map: dict[str, set[int]],
             allow: set | None = None) -> list[dict]:
    """Return phantom-attribution findings for one doc.

    ref_map: base_var -> set of module NUMBERS that reference it anywhere in code.
    A finding = a table row whose col-1 module references NONE of the row's vars.
    """
    allow = allow or set()
    fname = os.path.basename(rel_path)
    findings: list[dict] = []
    lines = text.splitlines()
    in_table = False           # currently inside an attribution table body
    armed = False              # a Provides-To/Receives-From header was just seen
    for i, line in enumerate(lines, start=1):
        if SECTION_RE.match(line) and "|" not in line:
            armed = True
            in_table = False
            continue
        if SEP_RE.match(line):        # the |---|---| separator: table body starts next
            if armed:
                in_table = True
            continue
        row = ROW_RE.match(line)
        if not row:
            # a blank / prose line ends the current table
            if line.strip() == "" or (not line.lstrip().startswith("|")):
                in_table = False
                armed = False
            continue
        cells = [c.strip() for c in row.group(1).split("|")]
        if not cells:
            continue
        # A header row (| Module | Variable | ... |) arms the table even without a sep line.
        if HEADER_CELL_RE.match(cells[0]):
            armed = True
            continue
        if not (in_table or armed) or len(cells) < 2:
            continue
        col1, col2 = cells[0], cells[1]
        mods = _mods_in_cell(col1)
        vars = _vars_in_cell(col2)
        if not mods or not vars:
            continue
        # vars that our ground truth actually knows about (skip unknown -> avoid FP)
        known = [v for v in vars if v in ref_map]
        if not known:
            continue
        scan_doc.rows_evaluated += 1  # coverage instrumentation (disambiguates 0 findings)
        for mod in mods:
            if any(mod in ref_map[v] for v in known):
                continue  # module references at least one of the row's vars -> OK
            key = f"{mod:02d}:{','.join(known)}"
            if (fname, key) in allow:
                continue
            findings.append({
                "file": rel_path, "line": i, "claimed_module": mod,
                "vars": known,
                "true_refs": sorted({m for v in known for m in ref_map[v]}),
                "row": line.strip()[:160],
            })
    return findings


scan_doc.rows_evaluated = 0  # coverage counter; reset by callers (see main / self_test)


def _ref_map_from_consumers(consumers=None) -> dict[str, set[int]]:
    """build_consumer_map (var -> {"NN_name"}) normalized to var -> {NN:int}.

    `consumers` is injectable (defaulting to the real build_consumer_map()) so the
    self-test can exercise this normalization directly. Pre-R58 it was dead to the
    test: it could be replaced with `raise` and the suite stayed green. Note this
    function is DUPLICATED verbatim in check_attribution_tables.py and
    check_attribution_prose.py -- the same duplication shape as the CROSS_IFACE_RE
    bug R57 had to fix at two sites. Keep both copies in sync.
    """
    src = consumers if consumers is not None else build_consumer_map()
    out: dict[str, set[int]] = {}
    for var, mods in src.items():
        nums = set()
        for m in mods:
            head = m.split("_", 1)[0]
            if head.isdigit():
                nums.add(int(head))
        out[strip_dims(var)] = nums
    return out


def _fmt(f: dict) -> str:
    return (f"{f['file']}:{f['line']}: [attribution-table] Module {f['claimed_module']:02d} "
            f"is listed for {f['vars']}, but code shows that var referenced only by "
            f"modules {f['true_refs']} (Module {f['claimed_module']:02d} references none of "
            f"the row's vars) -> likely phantom attribution. Row: {f['row']}")


def main() -> int:
    allow = load_allowlist()
    ref_map = _ref_map_from_consumers()
    if not ref_map:
        print(f"{CHECK_NAME}: WARNING could not build consumer map "
              f"(parent modules/ not found) - skipping.")
        return 0
    all_findings: list[dict] = []
    scan_doc.rows_evaluated = 0
    docs_with_rows = 0
    n_docs = 0
    for doc in sorted(DOCS_DIR.glob("module_*.md")):
        if doc.name.endswith("_notes.md"):
            continue
        n_docs += 1
        rel = f"modules/{doc.name}"
        before = scan_doc.rows_evaluated
        all_findings.extend(scan_doc(doc.read_text(), rel, ref_map, allow))
        if scan_doc.rows_evaluated > before:
            docs_with_rows += 1
    # Coverage line ALWAYS printed: a "0 findings" is meaningless without the denominator.
    # This check parses only the markdown-TABLE attribution format; docs expressing
    # attribution as prose (the majority) evaluate 0 rows and are NOT covered here.
    print(f"{CHECK_NAME}: coverage = {scan_doc.rows_evaluated} table rows evaluated across "
          f"{docs_with_rows}/{n_docs} module docs (table-format only; prose forms uncovered).")
    if all_findings:
        print(f"{CHECK_NAME}: {len(all_findings)} advisory phantom-attribution finding(s):")
        for f in all_findings:
            print("  " + _fmt(f))
    else:
        print(f"{CHECK_NAME}: 0 findings within covered rows "
              f"(NOT a corpus-clean claim — see coverage above).")
    return 0


def self_test() -> int:
    """Hermetic positive + negative control with an injected ref-map (no parent repo)."""
    # Ground truth: vm_land_forestry is referenced only by module 58 (the real R54 case);
    # vm_carbon_stock by 52 and 56.
    ref = {"vm_land_forestry": {58}, "vm_carbon_stock": {52, 56}, "vm_cost_fore": {11}}
    doc = (
        "#### 8.1 Provides To (Outputs)\n"
        "| Module | Variable | Desc | Cite |\n"
        "| --- | --- | --- | --- |\n"
        "| **10_land** | vm_land_forestry | wrong: only M58 reads it | x |\n"      # PHANTOM
        "| **58_peatland** | vm_land_forestry | correct | x |\n"                    # OK
        "| **52_carbon** / **56_ghg_policy** | vm_carbon_stock(j,...) | both read | x |\n"  # OK
        "| **11_costs** | vm_cost_fore | correct | x |\n"                           # OK
        "\n"
        "Some prose after the table mentioning Module 10 and vm_land_forestry.\n"  # must NOT flag
    )
    findings = scan_doc(doc, "modules/module_TEST.md", ref)
    keys = {(f["claimed_module"], tuple(f["vars"])) for f in findings}
    ok = True
    # positive: M10/vm_land_forestry MUST be flagged
    if (10, ("vm_land_forestry",)) not in keys:
        print("SELF-TEST FAIL: did not flag the planted phantom (M10 / vm_land_forestry)")
        ok = False
    # negatives: none of these may be flagged
    for bad in [(58, ("vm_land_forestry",)), (52, ("vm_carbon_stock",)),
                (56, ("vm_carbon_stock",)), (11, ("vm_cost_fore",))]:
        if bad in keys:
            print(f"SELF-TEST FAIL: false-positive on a correct row {bad}")
            ok = False
    # exactly one finding expected (the single phantom)
    if len(findings) != 1:
        print(f"SELF-TEST FAIL: expected exactly 1 finding, got {len(findings)}: {findings}")
        ok = False
    # ---- BARE-NUMBER LABEL form: `**58** (Peatland)` (added 2026-07-19) -------
    # This house convention was unreadable before MODNUM_LABEL_RE, silently
    # costing 51 rows / 4 docs. Pin BOTH arms: it must now be read, and the
    # precision guard (parenthesised name required) must still reject a bare
    # count / year / decimal, which would otherwise be misread as a module.
    bare_doc = (
        "#### 8.1 Provides To (Outputs)\n"
        "| Module | Variable | Desc |\n"
        "| --- | --- | --- |\n"
        "| **10** (land) | vm_land_forestry | wrong: only M58 reads it |\n"   # PHANTOM
        "| **58** (Peatland) | vm_land_forestry | correct |\n"                # OK
        "| 2020 (baseline) | vm_cost_fore | year, not a module |\n"           # must not read
    )
    bare_findings = scan_doc(bare_doc, "modules/module_TEST.md", ref)
    bare_keys = {(f["claimed_module"], tuple(f["vars"])) for f in bare_findings}
    if (10, ("vm_land_forestry",)) in bare_keys:
        print("  SELF-TEST PASS [bare-label]: `**10** (land)` read as module 10")
    else:
        print("  SELF-TEST FAIL [bare-label]: `**NN** (Name)` form not read")
        ok = False
    if (58, ("vm_land_forestry",)) in bare_keys or any(
            f["claimed_module"] == 2020 or f["claimed_module"] == 20
            for f in bare_findings):
        print("  SELF-TEST FAIL [bare-label]: correct row or a YEAR was misread")
        ok = False
    else:
        print("  SELF-TEST PASS [bare-label]: correct row clean, `2020 (baseline)` not a module")

    # ---- GROUND-TRUTH: _ref_map_from_consumers normalization ------------------
    # Pre-R58 this wrapper was dead to the test -- both self-tests inject a ref-map
    # ("no parent repo", per their own docstrings), so the function that BUILDS the
    # ref map was never called. Its extractor (build_consumer_map) is now covered in
    # check_consumer_attribution.py; this covers the normalization layered on top:
    # "70_livestock" -> 70, non-numeric dirs dropped, dims stripped from the key.
    _rm = _ref_map_from_consumers(consumers={
        "vm_x(i,j)": {"70_livestock", "29_cropland", "not_a_module"},
        "vm_y": {"11_costs"},
    })
    if _rm.get("vm_x") != {70, 29}:
        ok = False
        print(f"  SELF-TEST FAIL [ref-map-norm]: vm_x -> {_rm.get('vm_x')}, want {{70, 29}}")
    elif "vm_x(i,j)" in _rm:
        ok = False
        print("  SELF-TEST FAIL [ref-map-norm]: dims not stripped from var key")
    elif _rm.get("vm_y") != {11}:
        ok = False
        print(f"  SELF-TEST FAIL [ref-map-norm]: vm_y -> {_rm.get('vm_y')}, want {{11}}")
    else:
        print("  SELF-TEST PASS [ref-map-norm]: NN_name -> NN, non-numeric dropped, dims stripped")

    if ok:
        print("SELF-TEST PASS: planted phantom flagged, all correct rows clean.")
        print(f"SELFTEST_OK {CHECK_NAME}")  # sentinel required by selftest_validator.sh [4/5]
    else:
        print("SELF-TEST FAILED.")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(main())
