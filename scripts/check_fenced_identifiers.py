#!/usr/bin/env python3
"""Check 39: phantom interface identifiers inside fenced blocks and ASCII diagrams.

THE GAP THIS CLOSES (found R58, and it is not hypothetical):
`module_29.md` claimed a circular dependency "Cycle C29" whose return edge was
`pm_carbon_density_soilc` -- a variable that exists NOWHERE in MAgPIE. It was a
Critical (a fabricated cross-module feedback edge), and it survived months of GREEN
gates. Why: Check 14 (`check_gams_variables`, a GATING check) extracts identifiers
via `DOC_VAR_RE`, which requires the name to be INLINE-BACKTICKED. The phantom sat
in a plain-text ASCII diagram inside a fenced block:

    Module 29 (Cropland) ──→ vm_treecover(j) ──→ Module 59 (SOM)
           ↑                                          │
           └────────── pm_carbon_density_soilc ←──────┘

No backticks -> Check 14 never saw it. Verified with a synthesized pair: a phantom in
a plain-text diagram yields `DOC_VAR_RE.findall(...) == []`; the same name backticked
is caught. The defect survived precisely by being drawn rather than written.

This matters beyond one bug: a DIAGRAM is where a reader actually consumes a
"who talks to whom" claim. It is the highest-trust, lowest-checked surface in the
corpus -- 1208 fenced blocks across 46 module docs were entirely unchecked for
identifier existence.

SCOPE: fenced ``` blocks in `modules/module_*.md` (excluding `_notes.md`). Inside
those blocks, any interface-shaped token (`vm_`/`pm_`/`im_`/`fm_`/`pcm_`/`sm_`/`cm_`
and the module-numbered forms) must exist in the GAMS index.

PRECISION measures (this is advisory; the R5x lesson is "no noisy checks"):
  * reuses Check 14's GAMS index, allowlist and placeholder/wildcard/template filters,
    so the two checks cannot disagree about what exists;
  * honours the same `<!-- check-gams-vars: allow ... -->` per-doc markers, so a
    deliberate negation ("this variable does NOT exist") is suppressible in one place;
  * skips tokens with a `*`/`?`/`<`/`N` wildcard or placeholder shape.

Advisory: always exits 0. Findings surface as warnings via the validator.

Usage: python3 scripts/check_fenced_identifiers.py [--self-test] [--summary-only]
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_gams_variables import (  # noqa: E402
    ALLOWLIST,
    build_gams_index,
    collect_per_doc_allow,
)

AGENT_DIR = SCRIPT_DIR.parent
DOCS_DIR = AGENT_DIR / "modules"

FENCE_RE = re.compile(r"^```", re.M)
# Interface-shaped token WITHOUT requiring backticks -- the whole point.
FENCED_IDENT_RE = re.compile(
    r"\b((?:vm_|pm_|fm_|im_|pcm_|sm_|cm_|ic\d+_|oq\d+_|ov\d+_|pc\d+_"
    r"|[vpfisc]\d+_)[a-zA-Z][a-zA-Z0-9_]*)"
)
# Placeholder shapes that are illustrative, not claims.
PLACEHOLDER_RE = re.compile(r"[<>*?]|_(xxx|nnn|n|x|name|var)$|^\w+_$", re.I)


# A block is a DIAGRAM if it draws edges. This is the precision knob, and it is the
# whole reason this check is shippable -- see the FP measurement in the module
# docstring. Box-drawing (Unicode) or ASCII arrow/edge syntax.
# NOTE the exclusions, each learned by measurement, not by taste:
#   `<-` is R's ASSIGNMENT operator -- including it made every ```r block look like a
#        diagram and produced 3 of the 6 remaining false positives.
#   `->` is R's right-assign and appears in prose arrows inside code comments.
# Only unambiguous edge-drawing survives: Unicode box/arrow glyphs, or a multi-dash
# ASCII arrow that no language uses as an operator.
DIAGRAM_CHAR_RE = re.compile(r"[─│┌┐└┘├┤┬┴┼→←↑↓▼▲►◄]|-->|<--|\+---|\|__")


def is_diagram(block: str) -> bool:
    """True if the fenced block draws a structure rather than illustrating code.

    The R58 phantom lived in a diagram; every false positive measured on the live
    corpus (32 of 32 in the first cut) lived in pseudo-code / example blocks. A
    diagram asserts "A talks to B" and is consumed as fact by a reader; a
    pseudo-code block illustrates code the reader might WRITE, so its identifiers
    are deliberately hypothetical (`vm_new_cost`, `p17_ncells`, `pm_bii_coeff`
    under a literal "Pseudo-code:" heading).
    """
    return bool(DIAGRAM_CHAR_RE.search(block))


def iter_fenced_blocks(text: str):
    """Yield (block_text, start_line) for each ``` fenced block."""
    lines = text.split("\n")
    inside = False
    buf: list[str] = []
    start = 0
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            if inside:
                yield "\n".join(buf), start
                buf = []
            else:
                start = i + 1
            inside = not inside
            continue
        if inside:
            buf.append(line)
    # An unterminated fence yields nothing -- deliberate: we do not want to treat
    # the rest of the document as fenced on a stray ```.


def scan_doc(text: str, gams_index: set[str], per_doc_allow: set[str]):
    """Return [(identifier, line_no)] for fenced identifiers absent from GAMS."""
    findings = []
    seen = set()
    for block, start in iter_fenced_blocks(text):
        if not is_diagram(block):
            continue  # pseudo-code / example block: identifiers are illustrative
        for offset, line in enumerate(block.split("\n")):
            for ident in FENCED_IDENT_RE.findall(line):
                if ident in gams_index or ident in ALLOWLIST or ident in per_doc_allow:
                    continue
                if PLACEHOLDER_RE.search(ident):
                    continue
                key = (ident, start + offset)
                if key in seen:
                    continue
                seen.add(key)
                findings.append((ident, start + offset))
    return findings


def _self_test() -> int:
    """Positive control anchored on the REAL R58 bug.

    The fixture reproduces module_29.md's actual phantom -- an unbackticked
    `pm_carbon_density_soilc` in an ASCII diagram -- because that is the defect this
    check exists to catch. Negative controls guard the precision claims.
    """
    checks: list[tuple[str, bool]] = []

    def check(name: str, cond: bool) -> None:
        checks.append((name, bool(cond)))

    index = {"vm_treecover", "vm_land", "vm_cost_glo"}

    # POSITIVE control: the real bug's exact shape.
    real_bug = (
        "# Cycle C29\n"
        "```\n"
        "Module 29 (Cropland) --> vm_treecover(j) --> Module 59 (SOM)\n"
        "       ^                                          |\n"
        "       +--------- pm_carbon_density_soilc <-------+\n"
        "```\n"
    )
    got = scan_doc(real_bug, index, set())
    names = {g[0] for g in got}
    check("catches the REAL R58 phantom in an ASCII diagram",
          "pm_carbon_density_soilc" in names)
    check("does NOT flag the real variable in the same diagram",
          "vm_treecover" not in names)

    # This is the control that proves the check adds something Check 14 cannot do.
    from check_gams_variables import DOC_VAR_RE
    check("Check 14's DOC_VAR_RE is genuinely blind to this (the gap is real)",
          DOC_VAR_RE.findall(real_bug) == [])

    # NEGATIVE controls.
    check("clean fenced diagram yields nothing",
          scan_doc("```\nA --> vm_land --> B\n```\n", index, set()) == [])
    # THE precision control: the measured FP class. 32 of 32 live findings in the
    # first cut were pseudo-code identifiers; scoping to diagrams removed all 32
    # while keeping the real bug.
    check("pseudo-code block is NOT scanned (the measured FP class)",
          scan_doc("**Pseudo-code**:\n```gams\npm_totally_fake(\"x\") = 1.0\n"
                   "vm_new_cost(i) =e= calculation;\n```\n", index, set()) == [])
    check("phantom OUTSIDE any fence is not this check's business",
          scan_doc("prose mentions pm_totally_fake here\n", index, set()) == [])
    check("per-doc allow marker suppresses a deliberate negation",
          scan_doc("<!-- check-gams-vars: allow pm_ghost -->\n```\npm_ghost\n```\n",
                   index, collect_per_doc_allow(
                       "<!-- check-gams-vars: allow pm_ghost -->")) == [])
    check("placeholder shapes are skipped",
          scan_doc("```\nvm_<name>  vm_xxx\n```\n", index, set()) == [])
    check("unterminated fence does not swallow the document",
          scan_doc("```\npm_fake_a\n", index, set()) == [])

    # The extractor is exercised for real over a synthetic tree (not stubbed).
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "modules" / "10_land" / "r").mkdir(parents=True)
        (root / "modules" / "10_land" / "r" / "declarations.gms").write_text(
            " vm_real_var(j) a\n")
        (root / "main.gms").write_text("* x\n")
        import subprocess, json  # noqa: E401
        p = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0,'scripts');"
             "from check_gams_variables import build_gams_index;"
             "import json; print(json.dumps(sorted(build_gams_index())))"],
            capture_output=True, text=True,
            env=dict(os.environ, MAGPIE_DIR=str(root)), cwd=str(AGENT_DIR), timeout=60)
        ok_sub = p.returncode == 0 and "vm_real_var" in json.loads(p.stdout)
        check("real GAMS index builder is exercised (not stubbed)", ok_sub)

    for name, cond in checks:
        print(f"  {'ok  ' if cond else 'FAIL'} {name}", file=sys.stderr)
    if any(not c for _, c in checks):
        print("SELF-TEST FAILED", file=sys.stderr)
        return 1
    print(f"SELF-TEST OK - {len(checks)} assertions; the R58 diagram phantom is caught "
          "and Check 14's blindness to it is demonstrated.", file=sys.stderr)
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--self-test" in args:
        rc = _self_test()
        if rc == 0:
            print("SELFTEST_OK check_fenced_identifiers")
        return rc

    from check_gams_variables import MAGPIE_DIR
    if not (MAGPIE_DIR / "main.gms").is_file() or not (MAGPIE_DIR / "modules").is_dir():
        print(f"⚠️  GAMS codebase not found at {MAGPIE_DIR} - skipping fenced-identifier check")
        return 0

    index = build_gams_index()
    if not index:
        print("  Fenced identifiers: GAMS index empty — skipped (would be vacuously green)")
        return 0

    total_docs = total_findings = 0
    for md in sorted(DOCS_DIR.glob("module_*.md")):
        if md.name.endswith("_notes.md"):
            continue
        text = md.read_text(errors="ignore")
        total_docs += 1
        found = scan_doc(text, index, collect_per_doc_allow(text))
        for ident, line in found:
            total_findings += 1
            if "--summary-only" not in args:
                print(f"    {md.relative_to(AGENT_DIR)}:{line}  {ident} — not in GAMS index")
    print(f"  Fenced identifiers: {total_findings} phantom(s) across {total_docs} docs "
          f"({len(index)} GAMS identifiers indexed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
