#!/usr/bin/env python3
"""Check 20: Cross-reference '(default N)' parameter claims in module docs against source.

Pattern 13 in Bug_Taxonomy.md: docs assert defaults like ``s56_buffer_aff`` (default 0.5)
that can drift from the actual GAMS source (input.gms `/value/` blocks or
`$setglobal` declarations, optionally overridden in `config/default.cfg`).

Scope: matches backticked params with prefix s<N>_, c<N>_, sm_, cm_ followed by a
`(default <value>)` (or `default: <value>`) annotation on the SAME line.

Source-of-truth priority:
  1. `config/default.cfg` override (`cfg$gms$NAME <- VALUE`)
  2. Module's default realization input.gms (`scalar NAME ... / VALUE /` or `$setglobal NAME VALUE`)

Comparison normalises numeric thousands separators, currency prefixes, GAMS y-year
prefix (`y2030` == `2030`), and string casing. Mismatches are reported as
advisories (script always exits 0) since the regex deliberately favours recall.

Usage: python3 scripts/check_param_defaults.py [--verbose]
  --verbose: also print params that were skipped because source could not be located.
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.dirname(SCRIPT_DIR)
MAGPIE_DIR = os.path.dirname(AGENT_DIR)

DEFAULT_CFG = os.path.join(MAGPIE_DIR, "config", "default.cfg")
MODULES_DIR = os.path.join(MAGPIE_DIR, "modules")
DOCS_DIR = os.path.join(AGENT_DIR, "modules")
ALLOWLIST_PATH = os.path.join(AGENT_DIR, "audit", "advisory_allowlist.json")


def load_allowlist():
    """Return set of (file, key) tuples allowlisted for this checker."""
    if not os.path.exists(ALLOWLIST_PATH):
        return set()
    with open(ALLOWLIST_PATH) as f:
        data = json.load(f)
    return {
        (entry["file"], entry["key"])
        for entry in data.get("allowlist", [])
        if entry.get("check") == "check_param_defaults"
    }

# Param name in backticks followed by (default VALUE) on the same line.
# VALUE: number with optional commas/decimals, quoted string, bare identifier, or y-prefixed year.
PARAM_DEFAULT_RE = re.compile(
    r"""
    `(?P<name>(?:s|c)\d+_\w+|sm_\w+|cm_\w+)`     # backticked param
    [^\n]{0,80}?                                   # up to 80 chars of intervening text
    \(\s*[Dd]efault[:\s]+                          # (default or (Default with : or space
    \$?                                            # optional currency
    (?P<value>
          "[^"]+"                                  # quoted string
        | \d[\d,]*\.?\d*[eE][+-]?\d+               # scientific notation (1e+06, 2.5e-3)
        | \d[\d,]*\.?\d*                           # number (possibly with comma thousands or decimal)
        | y\d{4}                                   # GAMS year prefix
        | [a-zA-Z_][\w\-]*                         # bare identifier
    )
    """,
    re.VERBOSE,
)

# config/default.cfg: cfg$gms$NAME <- VALUE
CFG_DEFAULT_RE = re.compile(r'^cfg\$gms\$(\w+)\s*<-\s*"?([^"#\n]+?)"?\s*(?:#.*)?$')

# input.gms scalar: optional leading whitespace, NAME desc / VALUE /
# We anchor on `NAME` followed by anything and then `/value/`.
def make_scalar_re(name):
    return re.compile(
        r"^\s*" + re.escape(name) + r"\b[^\n]*?/\s*([^/\n]+?)\s*/",
        re.MULTILINE,
    )


def make_setglobal_re(name):
    return re.compile(
        r"\$setglobal\s+" + re.escape(name) + r"\s+(\S+)",
    )


def parse_default_cfg():
    """Return {param_name: value} from config/default.cfg."""
    out = {}
    if not os.path.isfile(DEFAULT_CFG):
        return out
    with open(DEFAULT_CFG) as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or "<-" not in line:
                continue
            m = CFG_DEFAULT_RE.match(line)
            if m:
                name = m.group(1)
                val = m.group(2).strip().strip('"').strip("'")
                out[name] = val
    return out


def module_default_realization(defaults_map, module_num):
    """Return the default realization directory for a module (or None)."""
    # config/default.cfg key is the module name (e.g., "residues", not "18_residues").
    # Find module directory NN_NAME, then look up NAME in defaults_map.
    for entry in os.listdir(MODULES_DIR):
        m = re.match(r"^(\d+)_(.+)$", entry)
        if m and m.group(1) == str(module_num).zfill(2):
            return defaults_map.get(m.group(2))
    return None


def module_dir_for(module_num):
    for entry in os.listdir(MODULES_DIR):
        m = re.match(r"^(\d+)_(.+)$", entry)
        if m and m.group(1) == str(module_num).zfill(2):
            return os.path.join(MODULES_DIR, entry)
    return None


def lookup_in_input_gms(param_name, module_num, default_real):
    """Return (value, file_path) from the default realization's input.gms, or (None, None)."""
    mdir = module_dir_for(module_num)
    if not mdir or not default_real:
        return (None, None)
    input_path = os.path.join(mdir, default_real, "input.gms")
    if not os.path.isfile(input_path):
        return (None, None)
    with open(input_path) as f:
        text = f.read()
    # Try scalar declaration first
    m = make_scalar_re(param_name).search(text)
    if m:
        return (m.group(1).strip(), input_path)
    # Then $setglobal
    m = make_setglobal_re(param_name).search(text)
    if m:
        return (m.group(1).strip(), input_path)
    return (None, None)


def normalize(value):
    """Normalise a value string for comparison.

    Returns ("number", float) or ("string", lowercased str) or (None, None).
    """
    if value is None:
        return (None, None)
    s = value.strip().strip('"').strip("'")
    s_orig = s
    s = s.lstrip("$")
    s = s.replace(",", "")
    # Strip GAMS year prefix: y2030 -> 2030
    ym = re.match(r"^y(\d{4})$", s)
    if ym:
        s = ym.group(1)
    try:
        return ("number", float(s))
    except ValueError:
        return ("string", s_orig.strip('"').strip("'").lower())


def values_match(a, b):
    na = normalize(a)
    nb = normalize(b)
    if na[0] is None or nb[0] is None:
        return False
    if na[0] == "number" and nb[0] == "number":
        # Handle inf/-inf identity (subtraction yields NaN)
        import math
        if math.isinf(na[1]) and math.isinf(nb[1]):
            return (na[1] > 0) == (nb[1] > 0)
        if math.isnan(na[1]) or math.isnan(nb[1]):
            return False
        denom = max(1.0, abs(na[1]), abs(nb[1]))
        return abs(na[1] - nb[1]) < 1e-6 * denom
    if na[0] == "string" and nb[0] == "string":
        return na[1] == nb[1]
    # Number vs string: try string match on both sides
    return False


def extract_module_num_from_param(name):
    """s56_x -> 56; c18_y -> 18; sm_z/cm_z -> None."""
    m = re.match(r"^[sc](\d+)_", name)
    if m:
        return int(m.group(1))
    return None


PLACEHOLDER_WORDS = {
    "same", "varies", "various", "depends", "above", "below", "see", "this",
    "n", "x", "value", "scenario", "auto",
}


def scan_doc(doc_path, defaults_map):
    """Return list of mismatch dicts for one doc."""
    mismatches = []
    skipped = []
    with open(doc_path) as f:
        lines = f.readlines()
    for line_no, line in enumerate(lines, 1):
        for m in PARAM_DEFAULT_RE.finditer(line):
            name = m.group("name")
            claimed = m.group("value")
            # Skip placeholder words like "(default: same as selected)"
            if claimed.lower().strip('"').strip("'") in PLACEHOLDER_WORDS:
                continue
            module_num = extract_module_num_from_param(name)
            # 1. config/default.cfg
            cfg_val = defaults_map.get(name)
            source = None
            actual = None
            if cfg_val is not None:
                actual = cfg_val
                source = "config/default.cfg"
            elif module_num is not None:
                default_real = module_default_realization(defaults_map, module_num)
                actual, src_path = lookup_in_input_gms(name, module_num, default_real)
                if src_path:
                    source = os.path.relpath(src_path, MAGPIE_DIR)
            if actual is None:
                skipped.append(
                    {"line": line_no, "name": name, "claimed": claimed, "reason": "source not found"}
                )
                continue
            if not values_match(claimed, actual):
                mismatches.append(
                    {
                        "line": line_no,
                        "name": name,
                        "claimed": claimed,
                        "actual": actual,
                        "source": source,
                    }
                )
    return mismatches, skipped


def self_test():
    """Positive + clean controls via scan_doc() with an injected defaults_map.

    Synthesize the known bug FIRST, then assert the check flags it:
      Positive: doc claims `s99_foo` (default 0.9) but config says 0.5 -> mismatch.
      Clean:    doc claims `s99_foo` (default 0.5) matching config       -> none.
    No real tree or config/default.cfg is touched (defaults_map is injected and
    cfg_val is found, so the input.gms lookup branch is never reached).
    Exits 0 (prints SELFTEST_OK) iff both hold; 1 otherwise.
    """
    import shutil
    import tempfile

    ok = True
    defaults_map = {"s99_foo": "0.5"}
    tmp = tempfile.mkdtemp(prefix="check20_selftest_")
    try:
        doc_path = os.path.join(tmp, "module_99.md")

        with open(doc_path, "w") as f:
            f.write("The buffer `s99_foo` (default 0.9) controls X.\n")
        mismatches, _skipped = scan_doc(doc_path, defaults_map)
        if any(m["name"] == "s99_foo" for m in mismatches):
            print(f"  SELF-TEST PASS [positive]: drifted default flagged "
                  f"(claimed {mismatches[0]['claimed']} vs actual {mismatches[0]['actual']})")
        else:
            print(f"  SELF-TEST FAIL [positive]: `s99_foo` 0.9-vs-0.5 drift NOT flagged; got {mismatches}")
            ok = False

        with open(doc_path, "w") as f:
            f.write("The buffer `s99_foo` (default 0.5) controls X.\n")
        mismatches_clean, _ = scan_doc(doc_path, defaults_map)
        if not mismatches_clean:
            print("  SELF-TEST PASS [clean]: matching default not flagged")
        else:
            print(f"  SELF-TEST FAIL [clean]: matching default wrongly flagged: {mismatches_clean}")
            ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("check_param_defaults self-test: PASS")
        print("SELFTEST_OK check_param_defaults")
        return 0
    print("check_param_defaults self-test: FAIL")
    return 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    verbose = "--verbose" in sys.argv
    defaults_map = parse_default_cfg()
    allowlist = load_allowlist()
    if not os.path.isdir(DOCS_DIR):
        print(f"  Error: docs directory missing: {DOCS_DIR}", file=sys.stderr)
        return 1

    total_docs = 0
    total_matches_scanned = 0
    total_mismatches = 0
    total_skipped = 0
    total_allowlisted = 0
    all_mismatches = []
    all_skipped = []

    for fname in sorted(os.listdir(DOCS_DIR)):
        if not re.match(r"^module_\d+\.md$", fname):
            continue
        doc_path = os.path.join(DOCS_DIR, fname)
        mismatches, skipped = scan_doc(doc_path, defaults_map)
        total_docs += 1
        # Quick re-scan just to count matches
        with open(doc_path) as f:
            content = f.read()
        total_matches_scanned += len(PARAM_DEFAULT_RE.findall(content))
        total_skipped += len(skipped)
        rel_path = f"modules/{fname}"
        for mm in mismatches:
            mm["doc"] = fname
            if (rel_path, mm["name"]) in allowlist:
                total_allowlisted += 1
                continue
            total_mismatches += 1
            all_mismatches.append(mm)
        for sk in skipped:
            sk["doc"] = fname
            all_skipped.append(sk)

    if all_mismatches:
        suffix = f" ({total_allowlisted} allowlisted)" if total_allowlisted else ""
        print(f"  Param defaults: {total_mismatches} advisory mismatch(es) in {total_docs} docs ({total_matches_scanned} claims scanned){suffix}")
        for mm in all_mismatches:
            print(
                f"    {mm['doc']}:{mm['line']}  `{mm['name']}` claims default '{mm['claimed']}' "
                f"but source says '{mm['actual']}' ({mm['source']})"
            )
    else:
        suffix = f", {total_allowlisted} allowlisted" if total_allowlisted else ""
        print(
            f"  Param defaults: {total_matches_scanned} claims scanned across {total_docs} docs, 0 mismatches "
            f"({total_skipped} skipped - source not located{suffix})"
        )

    if verbose and all_skipped:
        print("\n  Skipped (source not located):")
        for sk in all_skipped:
            print(f"    {sk['doc']}:{sk['line']}  `{sk['name']}` (claimed '{sk['claimed']}') - {sk['reason']}")

    # Advisory: always exit 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
