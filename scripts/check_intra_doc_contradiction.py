#!/usr/bin/env python3
"""Check 30: Intra-doc default contradiction — one scalar, two different defaults.

Bug class (R52, module_59): the SAME scalar's default value is stated differently in
two places of ONE doc. module_59.md said `s59_nitrogen_uptake` "(default: ... 0.0002
Mt N/Mha)" at one point and "**Default**: 0.2" at another — a self-contradiction
(1000x), which survived ~51 rounds because no probe compared the two mentions.

This HARDENS Check 20 (check_param_defaults / Pattern 13) for the same scalar but via
a DIFFERENT mechanism: doc-vs-doc, never doc-vs-unit-converted-source. Check 20
compares a doc default against the GAMS source and trips a known false positive on
s59_nitrogen_uptake (doc "200 kg N/ha" vs source "0.2 tN/ha" are the same quantity in
different units). Comparing two mentions WITHIN one doc sidesteps unit conversion
entirely: a doc should state its own scalar's default consistently.

Unit-FP avoidance (critical): each mention contributes exactly ONE "primary" value —
the first value token right after the default marker — NOT every number on the line.
A default annotation like "0.2 (200 kg N/ha)" yields 0.2, not {0.2, 200}; otherwise
the secondary "200 kg N/ha" gloss (present in BOTH the fixed mentions) would
manufacture a contradiction on the corrected doc. The R52 fix made both mentions lead
with `0.2`, so the fixed doc is clean; pre-fix, one mention led with `0.0002`/`200`.

Two doc syntaxes are read:
  Form A (inline): `s59_x` ... (default: VALUE)        — VALUE may be backtick/$-wrapped
  Form B (header): **s59_x** (unit)\n- **Default**: VALUE

Explicitly NOT read: `cfg$gms$NAME <- VALUE` override examples in "Typical
Modifications" sections (e.g. module_59.md:682 `cfg$gms$s59_nitrogen_uptake <- 0.3`),
which are illustrative scenario values, not default claims.

Known advisory limits (R53 adversarial lens, accepted): being doc-vs-doc, the
check can FP when one scalar is stated in two units with different leading numbers
("1000 kg" vs "1 t"), and can misattribute a default to an earlier backticked
scalar sharing the same line. It MISSES table-cell defaults, the `**Default
value**:` header variant, and a contradiction where both mentions lead with the
same wrong value (a uniformly-wrong doc is invisible to an intra-doc check — that
class is Check 20's job, vs source).

Advisory: always exits 0. Contradictions are surfaced as warnings by the validator.

Usage: python3 scripts/check_intra_doc_contradiction.py [--self-test]
"""

import json
import math
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.dirname(SCRIPT_DIR)
DOCS_DIR = os.path.join(AGENT_DIR, "modules")
ALLOWLIST_PATH = os.path.join(AGENT_DIR, "audit", "advisory_allowlist.json")

SCALAR = r"(?:s|c)\d+_\w+|sm_\w+|cm_\w+"
VALUE = r'"[^"]+"|\d[\d,]*\.?\d*(?:[eE][+-]?\d+)?|y\d{4}|[a-zA-Z_][\w\-]*'

# Form A: backticked scalar, then (default[:\s=] [`][$]VALUE) on the same line.
# The separator allows '=' so the "(default = X)" form (live in 6+ docs) is read
# (R53 lens FN-A). The value may carry a trailing % ("100% immobile"); normalize()
# folds %.
FORM_A_RE = re.compile(
    r"`(?P<name>" + SCALAR + r")`[^\n]{0,80}?"
    r"\(\s*[Dd]efault[:\s=]+`?\$?(?P<value>(?:" + VALUE + r")%?)"
)
# Form B header: a line whose bold token IS a scalar name.
FORM_B_HEAD_RE = re.compile(r"\*\*(?P<name>" + SCALAR + r")\*\*")
# Form B default line: **Default**: VALUE (optionally bulleted).
FORM_B_DEF_RE = re.compile(r"\*\*Default\*\*[:\s]+`?\$?(?P<value>(?:" + VALUE + r")%?)")

# Filler words that can follow "default " in prose ("default is X", "default for
# X") and must not be captured as the value (R53 lens FP-B). None is ever a legit
# GAMS default (those are numbers, identifiers, Inf, or years).
PLACEHOLDER = {"same", "varies", "various", "depends", "above", "below", "see", "n", "x",
               "value", "scenario", "auto", "is", "of", "the", "to", "as", "at", "be", "in", "for"}


def load_allowlist():
    if not os.path.exists(ALLOWLIST_PATH):
        return set()
    with open(ALLOWLIST_PATH) as f:
        data = json.load(f)
    return {
        (entry["file"], entry["key"])
        for entry in data.get("allowlist", [])
        if entry.get("check") == "check_intra_doc_contradiction"
    }


def normalize(value):
    """('number', float) | ('string', lowercased) | (None, None).

    A trailing % folds to a share (100% -> 1.0) so that a percent gloss and the
    raw share default of one scalar are not mistaken for a contradiction.
    """
    if value is None:
        return (None, None)
    s = value.strip().strip('"').strip("'").lstrip("$").replace(",", "")
    pct = s.endswith("%")
    if pct:
        s = s[:-1].strip()
    ym = re.match(r"^y(\d{4})$", s)
    if ym:
        s = ym.group(1)
    try:
        num = float(s)
        return ("number", num / 100.0 if pct else num)
    except ValueError:
        return ("string", value.strip().strip('"').strip("'").lower())


def values_match(a, b):
    na, nb = normalize(a), normalize(b)
    if na[0] is None or nb[0] is None:
        return False
    if na[0] == "number" and nb[0] == "number":
        # Inf == Inf (same sign): both "unlimited" defaults are consistent.
        if math.isinf(na[1]) and math.isinf(nb[1]):
            return (na[1] > 0) == (nb[1] > 0)
        if math.isnan(na[1]) or math.isnan(nb[1]):
            return False
        denom = max(1.0, abs(na[1]), abs(nb[1]))
        return abs(na[1] - nb[1]) < 1e-6 * denom
    if na[0] == "string" and nb[0] == "string":
        return na[1] == nb[1]
    return False


def collect_mentions(lines):
    """Return {scalar_name: [(line_no, value), ...]} of primary default claims."""
    mentions = {}

    def add(name, line_no, value):
        if value.lower().strip('"').strip("'") in PLACEHOLDER:
            return
        mentions.setdefault(name, []).append((line_no, value))

    for i, line in enumerate(lines, 1):
        if "cfg$gms$" in line:  # override examples are not default claims
            continue
        for m in FORM_A_RE.finditer(line):
            add(m.group("name"), i, m.group("value"))

    # Form B: a **scalar** header, then the next **Default**: within a few lines
    # (stop early if another scalar header intervenes).
    for i, line in enumerate(lines):
        hm = FORM_B_HEAD_RE.search(line)
        if not hm:
            continue
        name = hm.group("name")
        for j in range(i + 1, min(i + 5, len(lines))):
            if FORM_B_HEAD_RE.search(lines[j]) and not FORM_B_DEF_RE.search(lines[j]):
                break
            dm = FORM_B_DEF_RE.search(lines[j])
            if dm:
                add(name, j + 1, dm.group("value"))
                break
    return mentions


def distinct_values(pairs):
    """Collapse (line, value) pairs to representatives with distinct values."""
    reps = []
    for line_no, value in pairs:
        if not any(values_match(value, rv) for _, rv in reps):
            reps.append((line_no, value))
    return reps


def scan_doc(doc_path, allowlist=frozenset()):
    """Return list of contradiction dicts for one doc."""
    rel = "modules/" + os.path.basename(doc_path)
    with open(doc_path) as f:
        lines = f.readlines()
    findings = []
    for name, pairs in collect_mentions(lines).items():
        if (rel, name) in allowlist:
            continue
        reps = distinct_values(pairs)
        if len(reps) >= 2:
            findings.append({"name": name, "claims": reps})
    return findings


def self_test():
    """Synthesize the module_59 bug FIRST, then assert the check flags it.

    Controls (synthetic docs, no real tree touched):
      positive-real : pre-fix s59 lines (Form A '200...0.0002' vs Form B '0.2') -> flag
      positive-plain: `s12_foo` (default 0.5) vs (default 0.9)                  -> flag
      clean         : post-fix s59 lines (both lead with 0.2)                   -> none
      trap          : one 0.2 default + a cfg$gms$ <- 0.3 override example       -> none
    Exits 0 and prints SELFTEST_OK iff all four hold; 1 otherwise.
    """
    import shutil
    import tempfile

    ok = True
    tmp = tempfile.mkdtemp(prefix="check30_selftest_")
    try:
        doc = os.path.join(tmp, "module_99.md")

        # positive-real: the actual pre-fix module_59 mentions
        with open(doc, "w") as f:
            f.write("- `s59_nitrogen_uptake`: Maximum N uptake per ha (default: 200 kg N/ha = 0.0002 Mt N/Mha, `input.gms:9`)\n")
            f.write("\n**s59_nitrogen_uptake** (tN/ha)\n- **Default**: 0.2 (200 kg N/ha) (`input.gms:9`)\n")
        fnd = scan_doc(doc)
        if any(f["name"] == "s59_nitrogen_uptake" and len(f["claims"]) >= 2 for f in fnd):
            print("  SELF-TEST PASS [positive-real]: s59 pre-fix contradiction flagged ({})".format(
                next(f["claims"] for f in fnd if f["name"] == "s59_nitrogen_uptake")))
        else:
            print(f"  SELF-TEST FAIL [positive-real]: s59 contradiction NOT flagged; got {fnd}")
            ok = False

        # positive-plain: two clean inline defaults that disagree
        with open(doc, "w") as f:
            f.write("The buffer `s12_foo` (default 0.5) is used here.\n")
            f.write("Elsewhere `s12_foo` (default 0.9) is mentioned.\n")
        if any(f["name"] == "s12_foo" for f in scan_doc(doc)):
            print("  SELF-TEST PASS [positive-plain]: 0.5-vs-0.9 inline contradiction flagged")
        else:
            print(f"  SELF-TEST FAIL [positive-plain]: not flagged; got {scan_doc(doc)}")
            ok = False

        # clean: post-fix s59 (both mentions lead with 0.2)
        with open(doc, "w") as f:
            f.write("- `s59_nitrogen_uptake`: max N uptake (default: `0.2`, i.e. 0.2 tN/ha = 200 kg N/ha; 0.2 Mt N/Mha, `input.gms:9`)\n")
            f.write("\n**s59_nitrogen_uptake** (tN/ha)\n- **Default**: 0.2 (200 kg N/ha) (`input.gms:9`)\n")
        if not scan_doc(doc):
            print("  SELF-TEST PASS [clean]: post-fix consistent 0.2 not flagged")
        else:
            print(f"  SELF-TEST FAIL [clean]: post-fix wrongly flagged: {scan_doc(doc)}")
            ok = False

        # trap: a single real default plus a cfg override example with a different value
        with open(doc, "w") as f:
            f.write("**s59_nitrogen_uptake** (tN/ha)\n- **Default**: 0.2 (200 kg N/ha)\n")
            f.write("\n```r\ncfg$gms$s59_nitrogen_uptake <- 0.3   # Increase from 0.2 to 0.3 tN/ha\n```\n")
        if not scan_doc(doc):
            print("  SELF-TEST PASS [trap]: cfg$gms$ override (0.3) not mistaken for a second default")
        else:
            print(f"  SELF-TEST FAIL [trap]: override wrongly flagged as contradiction: {scan_doc(doc)}")
            ok = False

        # regression [inf]: two "Inf" defaults are consistent (module_58 FP class)
        with open(doc, "w") as f:
            f.write("- `s58_rewetting_switch`: rewetting cap (default: Inf, `presolve.gms:38`)\n")
            f.write("\n**s58_rewetting_switch**\n- **Default**: Inf (unlimited)\n")
        if not scan_doc(doc):
            print("  SELF-TEST PASS [regression: inf]: Inf-vs-Inf not flagged as a contradiction")
        else:
            print(f"  SELF-TEST FAIL [regression: inf]: Inf-vs-Inf wrongly flagged: {scan_doc(doc)}")
            ok = False

        # regression [percent]: 100% and 1 are the same share (module_38 FP class)
        with open(doc, "w") as f:
            f.write("| `s38_immobile` | 1 | share | crop-specific fraction (default: 100% immobile) |\n")
            f.write("Capital split by `s38_immobile` (default 1 = 100% immobile).\n")
        if not scan_doc(doc):
            print("  SELF-TEST PASS [regression: percent]: 100%-vs-1 share not flagged")
        else:
            print(f"  SELF-TEST FAIL [regression: percent]: 100%-vs-1 wrongly flagged: {scan_doc(doc)}")
            ok = False

        # FN-A [recall]: the `(default = X)` separator form (live in 6+ docs) must
        # be read, so a contradiction stated with '=' is not silently missed
        with open(doc, "w") as f:
            f.write("First `s56_x` (default = 1, capped) applies.\n")
            f.write("Later `s56_x` (default: 0) in the other case.\n")
        if any(f["name"] == "s56_x" for f in scan_doc(doc)):
            print("  SELF-TEST PASS [FN-A: = form]: `(default = X)` contradiction caught")
        else:
            print(f"  SELF-TEST FAIL [FN-A: = form]: missed; got {scan_doc(doc)}")
            ok = False

        # FP-B [precision]: `(default is X)` filler must not be read as the value "is"
        with open(doc, "w") as f:
            f.write("Here `s56_y` (default is 0.5) holds.\n")
            f.write("And `s56_y` (default: 0.5) elsewhere.\n")
        if not scan_doc(doc):
            print("  SELF-TEST PASS [FP-B: 'is' filler]: `(default is 0.5)` not read as 'is'")
        else:
            print(f"  SELF-TEST FAIL [FP-B: 'is' filler]: wrongly flagged: {scan_doc(doc)}")
            ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("check_intra_doc_contradiction self-test: PASS")
        print("SELFTEST_OK check_intra_doc_contradiction")
        return 0
    print("check_intra_doc_contradiction self-test: FAIL")
    return 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    if not os.path.isdir(DOCS_DIR):
        print(f"  Error: docs directory missing: {DOCS_DIR}", file=sys.stderr)
        return 1
    allowlist = load_allowlist()

    total_docs = 0
    all_findings = []
    for fname in sorted(os.listdir(DOCS_DIR)):
        if not re.match(r"^module_\d+\.md$", fname):
            continue
        total_docs += 1
        for fd in scan_doc(os.path.join(DOCS_DIR, fname), allowlist):
            fd["doc"] = fname
            all_findings.append(fd)

    if all_findings:
        print(f"  Intra-doc contradictions: {len(all_findings)} scalar(s) with conflicting defaults across {total_docs} docs")
        for fd in all_findings:
            claims = "; ".join(f"L{ln}={v}" for ln, v in fd["claims"])
            print(f"    {fd['doc']}  `{fd['name']}` stated as [{claims}]")
    else:
        print(f"  Intra-doc contradictions: 0 across {total_docs} docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
