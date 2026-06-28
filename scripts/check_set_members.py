#!/usr/bin/env python3
"""Check 29: Set-member enumeration drift in module docs vs canonical GAMS sets.

Bug class (R52, module_52): a doc enumerates the members of a CLOSED GAMS set but
invents members that do not exist and/or omits real ones. module_52.md listed the
`land` set as `(crop, past, primforest, secdforest, urban, other, plant_pri,
plant_sec)` — inventing `plant_pri`/`plant_sec` and omitting `forestry`. This
survived ~51 validation rounds because no probe ever touched that enumeration.

This check mechanizes the *class*: for each tracked closed set, parse its canonical
membership from the GAMS source, then scan module docs for inline enumerations of
the form `setname` ... (m1, m2, ...) and flag members that are not in the canonical
set.

PRECISION over recall (this is an advisory, and the R5x lesson is "no noisy
checks"). A parenthetical only qualifies as an enumeration of set S when:
  * it holds >= 2 comma-separated tokens,
  * every token is a bare set-member identifier (^[a-z][a-z0-9_]*$), and
  * >= 2 of those tokens are genuine members of S (so a coincidental parenthetical
    after `land`, e.g. `(mio. ha)`, is never mistaken for an enumeration).
The PRIMARY signal is an INVENTED member (a token provably not in the set) — a
near-certain error. Missing members are reported only as secondary context WHEN an
invented member is also present; a strict-subset enumeration with no invented token
is NOT flagged, because listing a subset of a set is usually legitimate. This
deliberately trades away pure-omission recall for a near-zero false-positive rate.

Scope: closed sets only (land family + carbon pools). Open/dynamic/large sets
(ac, regions, kall, mappings) are intentionally excluded — see CLOSED_SETS.

Forms covered: inline `setname` (a, b, ...) parentheticals AND contiguous
bulleted member runs (`- `member` ...`, matched to a set by membership overlap
with a clean-match-skip so a valid superset list isn't flagged as a subset).
Known advisory limits (precision-first recall gaps, not bugs): Oxford-"and" lists
(the non-exhaustive guard skips "..., and X"), enumerations keeping fewer than
half a set's real members, and lists where the set/member names are not backticked
or the member is not at the start of its bullet (e.g. "- Type `crop`:").

Advisory: always exits 0. Mismatches are surfaced as warnings by the validator.

Usage: python3 scripts/check_set_members.py [--self-test]
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.dirname(SCRIPT_DIR)
MAGPIE_DIR = os.path.dirname(AGENT_DIR)

DOCS_DIR = os.path.join(AGENT_DIR, "modules")
ALLOWLIST_PATH = os.path.join(AGENT_DIR, "audit", "advisory_allowlist.json")

# Tracked CLOSED sets -> GAMS source file (relative to MAGPIE_DIR) that declares
# their canonical `/ member, member /` membership. ag_pools is module-local (the
# default realization of M56); everything else lives in core/sets.gms.
CLOSED_SETS = {
    "land": "core/sets.gms",
    "land_ag": "core/sets.gms",
    "land_timber": "core/sets.gms",
    "land_forest": "core/sets.gms",
    "land_natveg": "core/sets.gms",
    "forest_type": "core/sets.gms",
    "c_pools": "core/sets.gms",
    "ag_pools": "modules/56_ghg_policy/price_aug22/sets.gms",
}

MEMBER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# Tokens that signal a non-exhaustive / prose list — skip such parentheticals.
NONEXHAUSTIVE_RE = re.compile(r"\.\.\.|\betc\b|e\.g\.|\bi\.e\.\b|\bsee\b|\band\b|\bor\b", re.IGNORECASE)
# A bullet line whose content STARTS with a backticked member token:
#   - `crop` - Cropland
BULLET_RE = re.compile(r"^\s*[-*]\s+`(?P<tok>[a-z][a-z0-9_]*)`")


def load_allowlist():
    """Return set of (file, key) tuples allowlisted for this checker."""
    if not os.path.exists(ALLOWLIST_PATH):
        return set()
    with open(ALLOWLIST_PATH) as f:
        data = json.load(f)
    return {
        (entry["file"], entry["key"])
        for entry in data.get("allowlist", [])
        if entry.get("check") == "check_set_members"
    }


def parse_set_members(text, name):
    """Extract members of a simple GAMS set NAME from a sets.gms body.

    Matches `NAME [(domain)] [description] / m1, m2, ... /` where the /.../ block
    may span multiple lines. The set name is anchored to a line start and word-
    bounded, so `land` does not match the `land_ag` declaration. Returns a set of
    lowercased member identifiers, or None if not found.

    Hardening (R53 adversarial lens): GAMS `*`-comment lines are stripped, and the
    opening `/` of the member block must be whitespace/line-delimited — so a `/`
    inside the free-text description (e.g. a unit like "tN/ha") is not mistaken for
    the block delimiter and used to parse description words as members.
    """
    text = "\n".join(l for l in text.split("\n") if not l.lstrip().startswith("*"))
    pat = re.compile(r"(?ms)^[ \t]*" + re.escape(name) + r"\b.*?(?:^|\s)/\s*([^/]*?)\s*/")
    m = pat.search(text)
    if not m:
        return None
    members = set()
    for tok in re.split(r"[,\s]+", m.group(1)):
        tok = tok.strip().lower()
        if MEMBER_RE.match(tok):
            members.add(tok)
    return members or None


def build_canonical_map():
    """Return {set_name: frozenset(members)} for all resolvable tracked sets."""
    file_cache = {}
    out = {}
    for name, rel in CLOSED_SETS.items():
        path = os.path.join(MAGPIE_DIR, rel)
        if path not in file_cache:
            file_cache[path] = open(path).read() if os.path.isfile(path) else None
        text = file_cache[path]
        if text is None:
            continue
        members = parse_set_members(text, name)
        if members:
            out[name] = frozenset(members)
    return out


def _eval_run(tokens, canonical_map, require_purity=True):
    """Evaluate a set of enumerated member tokens against the tracked sets.

    Returns (set_name, invented_sorted, missing_sorted) if the tokens look like a
    botched enumeration of some set, else None.

    Clean-match-skip: if the tokens cleanly enumerate ANY set (coverage met, zero
    invented), the run is a VALID enumeration -> None. This is essential for the
    set-name-agnostic bulleted form: {vegc,litc,soilc} is a clean `c_pools` list,
    so it must NOT be flagged as `ag_pools` (={vegc,litc}) plus an invented soilc.
    Otherwise flag the best-covered set whose listed tokens are mostly real members
    (purity) — a real botched enumeration lists mostly-right members plus a few
    wrong ones.
    """
    tokenset = set(tokens)
    scored = []
    for set_name, canonical in canonical_map.items():
        real = tokenset & canonical
        coverage = max(2, (len(canonical) + 1) // 2)
        invented = tokenset - canonical
        # clean-match-skip: a run that cleanly enumerates ANY set (coverage met,
        # nothing invented) is a valid enumeration -> never a drift.
        if len(real) >= coverage and not invented:
            return None
        scored.append((len(real), len(canonical), set_name, canonical, real, invented, coverage))
    # Attribute the run to the set that best EXPLAINS it (most real members, then
    # the larger set on ties), and flag only if THAT set itself qualifies. Prevents
    # a near-miss of a big set (e.g. land, below its coverage floor) being
    # misattributed to a small overlapping set (land_ag) whose members are common
    # words — which would brand a genuine member of the big set as "invented".
    scored.sort(key=lambda c: (-c[0], -c[1], c[2]))
    best_real, _, set_name, canonical, real, invented, coverage = scored[0]
    if best_real < coverage or not invented:
        return None
    if require_purity and len(real) < len(invented):
        return None
    return set_name, sorted(invented), sorted(canonical - tokenset)


def _scan_bulleted(lines, canonical_map, allowlist, rel, findings):
    """Detect contiguous runs of `- `member`` bullets and flag botched ones.

    Unlike the inline form there is no set-name anchor, so the run is matched to a
    set by membership overlap with the clean-match-skip + purity guards in
    _eval_run. Runs of unrelated backticked tokens (variables, products) fall below
    the coverage floor and are ignored.
    """
    # Split bullets into runs, breaking on a non-bullet line OR an indentation
    # change — so an indented sub-bullet breakdown (e.g. crop -> tece/maiz) is NOT
    # merged into its parent run and mistaken for one flat enumeration.
    runs = []
    cur = []
    cur_indent = None
    for line_no, line in enumerate(lines, 1):
        m = BULLET_RE.match(line)
        if m:
            indent = len(line) - len(line.lstrip())
            if cur and indent != cur_indent:
                runs.append(cur)
                cur = []
            if not cur:
                cur_indent = indent
            cur.append((line_no, m.group("tok").lower()))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)

    for run in runs:
        if len(run) < 2:
            continue
        res = _eval_run([t for _, t in run], canonical_map, require_purity=True)
        if not res:
            continue
        set_name, invented, missing = res
        if (rel, set_name) in allowlist:
            continue
        inv = set(invented)
        line_no = next((ln for ln, t in run if t in inv), run[0][0])
        findings.append({"line": line_no, "set": set_name,
                         "invented": invented, "missing": missing})


def scan_doc(doc_path, canonical_map, allowlist=frozenset()):
    """Return list of finding dicts for one doc."""
    findings = []
    with open(doc_path) as f:
        lines = f.readlines()
    rel = "modules/" + os.path.basename(doc_path)
    for set_name, canonical in canonical_map.items():
        if (rel, set_name) in allowlist:
            continue
        # `setname` then up to 60 non-paren chars then ( list ) on the same line.
        enum_re = re.compile(r"`" + re.escape(set_name) + r"`[^`\n(]{0,60}?\(([^()\n]+)\)")
        for line_no, line in enumerate(lines, 1):
            for m in enum_re.finditer(line):
                list_text = m.group(1)
                if NONEXHAUSTIVE_RE.search(list_text):
                    continue
                tokens = [t.strip().lower() for t in list_text.split(",")]
                tokens = [t for t in tokens if t]
                if len(tokens) < 2:
                    continue
                if not all(MEMBER_RE.match(t) for t in tokens):
                    continue
                tokenset = set(tokens)
                # Require the list to cover at least HALF the canonical set. A real
                # botched enumeration lists most of the set (module_52 listed 6 of
                # 7 land members); a coincidental prose parenthetical near `land`
                # (whose members crop/past/other/urban double as English words)
                # lists only a couple. This is the FP-D guard from the R53 lens.
                min_real = max(2, (len(canonical) + 1) // 2)
                if len(tokenset & canonical) < min_real:
                    continue  # not recognizably an enumeration of THIS set
                invented = tokenset - canonical
                if not invented:
                    continue  # subset / exact match — not flagged (precision)
                findings.append(
                    {
                        "line": line_no,
                        "set": set_name,
                        "invented": sorted(invented),
                        "missing": sorted(canonical - tokenset),
                    }
                )
    _scan_bulleted(lines, canonical_map, allowlist, rel, findings)
    return findings


def self_test():
    """Synthesize the module_52 bug FIRST, then assert the check flags it.

    Controls (all against an injected canonical_map, no real tree touched):
      positive : `land` (... plant_pri, plant_sec) -> invented flagged, forestry missing
      clean    : `land` (canonical 7) -> nothing
      negative1: `land` (mio. ha)     -> not an enumeration (1 token) -> nothing
      negative2: `land` (primforest, secdforest, other) subset, no invented -> nothing
    Exits 0 and prints SELFTEST_OK iff all four hold; 1 otherwise.
    """
    import shutil
    import tempfile

    canonical_map = {
        "land": frozenset({"crop", "past", "forestry", "primforest", "secdforest", "urban", "other"}),
        "c_pools": frozenset({"vegc", "litc", "soilc"}),
        "ag_pools": frozenset({"vegc", "litc"}),  # subset of c_pools -> overlap trap
        "land_ag": frozenset({"crop", "past"}),  # small subset of land -> misattribution trap
        "land_timber": frozenset({"forestry", "primforest", "secdforest", "other"}),
    }
    ok = True
    tmp = tempfile.mkdtemp(prefix="check29_selftest_")
    try:
        doc = os.path.join(tmp, "module_99.md")

        # positive
        with open(doc, "w") as f:
            f.write("  - `land`: Land types (crop, past, primforest, secdforest, urban, other, plant_pri, plant_sec)\n")
        fnd = scan_doc(doc, canonical_map)
        if any(f["set"] == "land" and "plant_pri" in f["invented"] and "plant_sec" in f["invented"]
               and "forestry" in f["missing"] for f in fnd):
            print("  SELF-TEST PASS [positive]: invented plant_pri/plant_sec flagged, forestry reported missing")
        else:
            print(f"  SELF-TEST FAIL [positive]: module_52 land bug NOT flagged; got {fnd}")
            ok = False

        # clean
        with open(doc, "w") as f:
            f.write("  - `land`: Land types (crop, past, forestry, primforest, secdforest, urban, other)\n")
        if not scan_doc(doc, canonical_map):
            print("  SELF-TEST PASS [clean]: canonical enumeration not flagged")
        else:
            print(f"  SELF-TEST FAIL [clean]: canonical enumeration wrongly flagged: {scan_doc(doc, canonical_map)}")
            ok = False

        # negative1: a unit parenthetical, not an enumeration
        with open(doc, "w") as f:
            f.write("The `land` pools are measured in (mio. ha) throughout.\n")
        if not scan_doc(doc, canonical_map):
            print("  SELF-TEST PASS [neg: unit paren]: `land` (mio. ha) not mistaken for an enumeration")
        else:
            print(f"  SELF-TEST FAIL [neg: unit paren]: wrongly flagged: {scan_doc(doc, canonical_map)}")
            ok = False

        # negative2: legitimate subset, no invented member
        with open(doc, "w") as f:
            f.write("Natural vegetation is the `land` subset (primforest, secdforest, other).\n")
        if not scan_doc(doc, canonical_map):
            print("  SELF-TEST PASS [neg: subset]: subset enumeration with no invented member not flagged")
        else:
            print(f"  SELF-TEST FAIL [neg: subset]: wrongly flagged: {scan_doc(doc, canonical_map)}")
            ok = False

        # negative3 [FP-D]: coincidental prose parenthetical near `land` (only 2 of
        # 7 members present -> below the half-coverage floor) must NOT be flagged
        with open(doc, "w") as f:
            f.write("Over time `land` dynamics shift (other, urban, future) across scenarios.\n")
        if not scan_doc(doc, canonical_map):
            print("  SELF-TEST PASS [neg: prose paren]: low-coverage prose list near `land` not flagged")
        else:
            print(f"  SELF-TEST FAIL [neg: prose paren]: wrongly flagged: {scan_doc(doc, canonical_map)}")
            ok = False

        # parser robustness [P1]: a '/' in the description (e.g. a unit "tN/ha")
        # must not be mistaken for the member-block delimiter
        stress = parse_set_members("  foo Max rate in tN/ha units\n     / a, b, c /\n", "foo")
        if stress == {"a", "b", "c"}:
            print("  SELF-TEST PASS [parser: slash-in-desc]: 'tN/ha' description not parsed as members")
        else:
            print(f"  SELF-TEST FAIL [parser: slash-in-desc]: got {stress}")
            ok = False

        # bulleted [extension]: the module_52 bulleted-list form must flag, AND the
        # {vegc,litc,soilc} carbon-pools run must NOT be mis-flagged as ag_pools
        # (clean-match-skip: it cleanly enumerates c_pools)
        with open(doc, "w") as f:
            f.write("**Land types**:\n")
            for t in ["crop", "past", "primforest", "secdforest", "urban", "other", "plant_pri", "plant_sec"]:
                f.write(f"- `{t}` - description\n")
            f.write("\n**Carbon pools**:\n")
            for t in ["vegc", "litc", "soilc"]:
                f.write(f"- `{t}` - description\n")
        bf = scan_doc(doc, canonical_map)
        land_hit = [f for f in bf if f["set"] == "land" and "plant_pri" in f["invented"]]
        pool_fp = [f for f in bf if f["set"] in ("c_pools", "ag_pools")]
        if land_hit and not pool_fp:
            print("  SELF-TEST PASS [bulleted]: bulleted land bug flagged; {vegc,litc,soilc} not mis-flagged as ag_pools")
        else:
            print(f"  SELF-TEST FAIL [bulleted]: got {bf}")
            ok = False

        # SET-FP1 [re-lens]: an indented sub-bullet breakdown (crop -> tece/maiz
        # children) must NOT merge into the parent run and look like a land_ag bug
        with open(doc, "w") as f:
            f.write("- `crop` cropland, split into:\n")
            f.write("  - `tece` temperate cereals\n")
            f.write("  - `maiz` maize\n")
            f.write("- `past` pasture\n")
        if not scan_doc(doc, canonical_map):
            print("  SELF-TEST PASS [bulleted: nested sub-bullets]: indented children not merged into parent run")
        else:
            print(f"  SELF-TEST FAIL [bulleted: nested sub-bullets]: wrongly flagged: {scan_doc(doc, canonical_map)}")
            ok = False

        # SET-FP2 [re-lens]: a near-miss of `land` (3 of 7 members + 1 outsider)
        # must NOT be misattributed to the small overlapping `land_ag`, which would
        # brand the real `land` member `forestry` as invented
        with open(doc, "w") as f:
            for t in ["crop", "past", "forestry", "rangeland"]:
                f.write(f"- `{t}` - description\n")
        if not scan_doc(doc, canonical_map):
            print("  SELF-TEST PASS [bulleted: small-set misattribution]: land near-miss not misattributed to land_ag")
        else:
            print(f"  SELF-TEST FAIL [bulleted: small-set misattribution]: wrongly flagged: {scan_doc(doc, canonical_map)}")
            ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("check_set_members self-test: PASS")
        print("SELFTEST_OK check_set_members")
        return 0
    print("check_set_members self-test: FAIL")
    return 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    if not os.path.isdir(DOCS_DIR):
        print(f"  Error: docs directory missing: {DOCS_DIR}", file=sys.stderr)
        return 1

    canonical_map = build_canonical_map()
    if not canonical_map:
        print("  Set members: no canonical sets resolved (sets.gms missing?) — skipped")
        return 0
    allowlist = load_allowlist()

    total_docs = 0
    all_findings = []
    for fname in sorted(os.listdir(DOCS_DIR)):
        if not re.match(r"^module_\d+\.md$", fname):
            continue
        total_docs += 1
        for fd in scan_doc(os.path.join(DOCS_DIR, fname), canonical_map, allowlist):
            fd["doc"] = fname
            all_findings.append(fd)

    sets_desc = ",".join(sorted(canonical_map))
    if all_findings:
        print(f"  Set members: {len(all_findings)} enumeration drift(s) in {total_docs} docs "
              f"[{len(canonical_map)} closed sets: {sets_desc}]")
        for fd in all_findings:
            note = ""
            if fd["missing"]:
                note = f"; also missing {', '.join(fd['missing'])}"
            print(f"    {fd['doc']}:{fd['line']}  `{fd['set']}` enumeration invents "
                  f"{', '.join(fd['invented'])}{note}")
    else:
        print(f"  Set members: 0 mismatches across {total_docs} docs "
              f"[{len(canonical_map)} closed sets: {sets_desc}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
