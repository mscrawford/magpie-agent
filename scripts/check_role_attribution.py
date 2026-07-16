#!/usr/bin/env python3
"""Check 31 - verify documentation DECLARED/PROVIDER attribution claims vs GAMS code.

Mechanizes the FP-safe core of MANDATE 18's DECLARED half (the DECLARED/POPULATED/READ
role vein) at validate-time. Companion to Check 29/30 (R53) and to the answer-time
`producer_declaration` verifier in verifiers.md.

Relationship to Check 22 (check_consumer_attribution): Check 22 verifies CONSUMER sets and
builds the declarer map (`build_producer_map`) ONLY as a count-subtrahend / skip-filter - it
never compares a doc's "declared in / provided by Module X" claim against that map. Check 31
does exactly that comparison. Disjoint trigger set, ground-truth use, and error class.

For each modules/module_NN.md it finds explicit attribution claims binding a backticked
interface variable to a module number:
  - "`var` ... declared in Module X" / "Declared in: Module X" / "(declared in MX)"
  - "`var` ... provided by Module X" / "Provided by Module X"
  - "Module X provides `var` (to Y)"          (the "X provides var" form)
and verifies X against the module that actually DECLARES var (declarations.gms).

Flag conditions (tiered by trigger precision):
  - declared-in : flag iff declarer is known + unambiguous + != X.  ("declared" is
                  unambiguous = declarations.gms, so a mismatch is a real bug.)
  - provided/provides : flag iff declarer is a specific module != X AND X does NOT reference
                  var in ANY of its *.gms (phantom). A module that genuinely POPULATES a slice
                  or READS var is in the reference set, so legitimate "provides its slice"
                  claims (e.g. land modules and vm_bv) are NOT flagged.

Universal skips (FP-safety): var not declared in any module (core-/input.gms-declared, or
unknown) -> skip; ambiguous declarer (multi-module "" sentinel) -> skip; non-interface token
-> skip; genuine historical/changelog markers -> skip. The claimed module number is anchored
to the trigger phrase, so the "declared in M_X, not M_Y" contrast idiom captures M_X
(asserted), never M_Y (negated).

Out of scope (deliberately, to stay precise): bare "Module X (var-list)" dependency/input
groupings and "Module X: `var`" colon-lists conflate declare/populate/consume and are
FP-prone to parse; those remain with the answer-time verifier + manual audit.

Scope: modules/module_NN.md only (matches Check 29/30).
Usage: python3 check_role_attribution.py [--self-test]
Exit: main() returns 0 always (advisory); --self-test returns 0/1.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_consumer_attribution import (  # noqa: E402
    build_consumer_map,
    build_producer_map,
    is_interface_var,
    strip_dims,
)

AGENT_DIR = SCRIPT_DIR.parent
DOCS_DIR = AGENT_DIR / "modules"
ALLOWLIST_PATH = AGENT_DIR / "audit" / "advisory_allowlist.json"
CHECK_NAME = "check_role_attribution"

# Backticked token that looks like an identifier, optionally with (dims).
BACKTICK_VAR_RE = re.compile(r"`([a-zA-Z][a-zA-Z0-9_]*(?:\([^`]*\))?)`")

# Trigger: "declared in [Module|M] NN" (optionally "Declared in: Module NN").
DECLARED_RE = re.compile(r"declared\s+in[\s:*]*(?:module\s+|m)?(\d{1,2})\b", re.IGNORECASE)
# Trigger: "provided by [Module|M] NN". [\s:*]* tolerates markdown bold/colon.
PROVIDED_RE = re.compile(r"provided\s+by[\s:*]*(?:module\s+|m)?(\d{1,2})\b", re.IGNORECASE)
# Trigger: "[Module] NN provides `var`" -> captures provider number AND the var directly.
PROVIDES_RE = re.compile(r"(?:module\s+)?(\d{1,2})\s+provides\s+`([^`]+)`", re.IGNORECASE)
# Structured field line ("- **Declared in**: Module X") whose variable lives in a preceding
# header. ONLY such field lines use the header-context var fallback; arbitrary prose
# "...(declared in MX)..." must carry its own inline backticked var (avoids mis-binding a
# stale header var to a prose mention - the module_17.md:772 vm_supply/vm_prod_reg FP).
FIELD_RE = re.compile(r"^\s*[-*]?\s*\*\*\s*(?:declared|provided)\b", re.IGNORECASE)

# Genuine historical / changelog wording -> skip the line (NOT the "not Module Y"
# contrast, which the trigger-anchoring already handles correctly).
HISTORICAL_RE = re.compile(
    r"\b(corrected|previously|used to be|was declared|changelog|deprecat|R\d+\s+audit|"
    r"earlier (?:draft|rubric)|formerly)\b",
    re.IGNORECASE,
)


def parse_allowlist(data) -> set[tuple[str, str]]:
    """Return {(doc_file, var)} pairs allow-listed for this check.

    Split out from load_allowlist() so the suppression path is actually assertable:
    R57/W0a measured load_allowlist as DEAD to this checker's --self-test (it could be
    replaced with `raise` and the self-test stayed green), which is exactly how the
    key bug below survived.

    R57 FIX: this read only "entries", but audit/advisory_allowlist.json keys its rows
    under "allowlist" -- so this checker's suppression list was silently ALWAYS EMPTY.
    Latent rather than active (no rows currently target check_role_attribution), but
    any allowlist entry added for it would have been ignored without a word. Accept
    both keys, as check_attribution_omissions.py already does.
    """
    rows = data if isinstance(data, list) else (
        data.get("allowlist") or data.get("entries") or [])
    return {(e.get("file", ""), e.get("key", "")) for e in rows
            if e.get("check") == CHECK_NAME}


def load_allowlist() -> set[tuple[str, str]]:
    """I/O wrapper around parse_allowlist()."""
    if not ALLOWLIST_PATH.exists():
        return set()
    try:
        return parse_allowlist(json.loads(ALLOWLIST_PATH.read_text()))
    except (ValueError, OSError):
        return set()


def declarer_num(var: str, producers: dict) -> int | None:
    """Module number that declares `var`, or None if unknown/ambiguous (-> skip)."""
    base = strip_dims(var)
    if not is_interface_var(base):
        return None
    p = producers.get(base)
    if not p:  # None (not declared in modules/) or "" (ambiguous) -> skip
        return None
    head = p.split("_", 1)[0]
    return int(head) if head.isdigit() else None


def references_var(claimed: int, var: str, consumers: dict) -> bool:
    """True if the claimed module references var (declares/populates/reads) in any *.gms."""
    base = strip_dims(var)
    for d in consumers.get(base, set()):
        head = d.split("_", 1)[0]
        if head.isdigit() and int(head) == claimed:
            return True
    return False


def scan_doc(text: str, rel_path: str, producers: dict, consumers: dict,
             allow: set | None = None) -> list[dict]:
    allow = allow or set()
    fname = os.path.basename(rel_path)
    findings: list[dict] = []
    ctx_var = None    # single interface var named in the most recent header/bold-subject line
    ctx_line = -100
    header_re = re.compile(r"^\s{0,3}(?:#{1,6}\s|\*\*)")
    for lineno, line in enumerate(text.splitlines(), start=1):
        if HISTORICAL_RE.search(line):
            continue
        line_vars = [
            (m.start(), m.group(1))
            for m in BACKTICK_VAR_RE.finditer(line)
            if is_interface_var(strip_dims(m.group(1)))
        ]
        # A header / bold-subject line naming exactly one interface var sets the
        # variable context for a following structured "**Declared in**:" field.
        if header_re.match(line) and len(line_vars) == 1:
            ctx_var, ctx_line = line_vars[0][1], lineno

        # Collect (var, claimed_num, kind) claims on this line.
        claims: list[tuple[str, int, str]] = []

        # "X provides `var`" - var captured directly by the regex.
        for m in PROVIDES_RE.finditer(line):
            claims.append((m.group(2), int(m.group(1)), "provides"))

        # "declared in NN" / "provided by NN" - bind to the var. Prefer the single
        # inline var; else fall back to the recent header-context var (structured
        # "**Declared in**: Module X" field). Multi-var lines are ambiguous -> skipped
        # (lowers recall, not precision).
        anchored = [(m.start(), int(m.group(1)), "declared") for m in DECLARED_RE.finditer(line)]
        anchored += [(m.start(), int(m.group(1)), "provided") for m in PROVIDED_RE.finditer(line)]
        if anchored:
            if len(line_vars) == 1:
                var = line_vars[0][1]
            elif (not line_vars and ctx_var is not None and (lineno - ctx_line) <= 8
                  and FIELD_RE.match(line)):
                var = ctx_var
            else:
                var = None
            if var is not None:
                for _pos, num, kind in anchored:
                    claims.append((var, num, kind))

        for var, claimed, kind in claims:
            base = strip_dims(var)
            if (fname, base) in allow:
                continue
            decl = declarer_num(var, producers)
            if decl is None or decl == claimed:
                continue  # unknown/ambiguous, or claim is correct
            if kind in ("provides", "provided"):
                # only flag a phantom: claimed module doesn't touch var at all
                if references_var(claimed, var, consumers):
                    continue
            findings.append({
                "line": lineno, "var": base, "claimed": claimed,
                "declarer": decl, "kind": kind, "doc": fname,
            })
    return findings


def _fmt(f: dict) -> str:
    verb = "declared in" if f["kind"] == "declared" else "attributed to"
    return (f"    {f['doc']}:{f['line']}  `{f['var']}` {verb} Module {f['claimed']:02d}, "
            f"but declarations.gms shows Module {f['declarer']:02d} "
            f"({'wrong declarer' if f['kind']=='declared' else 'phantom provider'})")


def main() -> int:
    producers = build_producer_map()
    consumers = build_consumer_map()
    allow = load_allowlist()
    all_findings: list[dict] = []
    n_docs = 0
    if DOCS_DIR.is_dir():
        for fname in sorted(os.listdir(DOCS_DIR)):
            if not re.match(r"^module_\d+\.md$", fname):
                continue
            n_docs += 1
            text = (DOCS_DIR / fname).read_text(errors="replace")
            all_findings.extend(scan_doc(text, fname, producers, consumers, allow))

    if not all_findings:
        print(f"  Role attribution: 0 mismatches across {n_docs} module docs "
              f"(declared-in / provider claims vs declarations.gms)")
    else:
        print(f"  Role attribution: {len(all_findings)} declarer/provider mismatch(es) "
              f"across {n_docs} module docs")
        for f in all_findings:
            print(_fmt(f))
    return 0


def self_test() -> int:
    ok = True
    producers = {
        "vm_carbon_stock": "56_ghg_policy",
        "pm_max_forest_est": "35_natveg",
        "vm_prod": "17_production",
        "vm_bv": "44_biodiversity",
        "vm_ambig": "",  # ambiguous (multi-module) sentinel
    }
    consumers = {
        "vm_carbon_stock": {"56_ghg_policy", "52_carbon", "31_past", "29_cropland", "32_forestry"},
        "pm_max_forest_est": {"35_natveg", "32_forestry"},
        "vm_prod": {"17_production", "30_croparea", "38_factor_costs", "42_water_demand"},
        "vm_bv": {"44_biodiversity", "29_cropland", "31_past", "32_forestry"},
    }
    # Each case: (label, line, expect_flag)
    cases = [
        # POSITIVE controls (the bug class - must flag)
        ("pos-declared-mismatch", "`vm_carbon_stock` is declared in Module 52.", True),
        ("pos-provides-phantom", "Module 10 provides `pm_max_forest_est` to 32.", True),
        # NEGATIVE controls (must NOT flag)
        ("neg-declared-correct", "`vm_carbon_stock` is declared in Module 56.", False),
        ("neg-contrast-idiom", "`vm_carbon_stock` is declared in Module 56, not Module 52.", False),
        ("neg-consumer-claim", "`vm_carbon_stock` is read by Module 52.", False),
        ("neg-legit-populator", "Module 31 provides `vm_carbon_stock` (its pasture slice).", False),
        ("neg-core-unknown-var", "`im_unknown_core` is declared in Module 9.", False),
        ("neg-ambiguous-declarer", "`vm_ambig` is declared in Module 10.", False),
        ("neg-bare-provides-via", "Pasture provides livestock feed via `vm_prod`.", False),
        ("neg-historical-marker", "`vm_carbon_stock` was declared in Module 52 (corrected R20).", False),
    ]
    for label, line, expect in cases:
        fnd = scan_doc(line + "\n", "module_99.md", producers, consumers)
        got = len(fnd) > 0
        if got == expect:
            print(f"  SELF-TEST PASS [{label}]")
        else:
            print(f"  SELF-TEST FAIL [{label}]: expected flag={expect}, got {fnd}")
            ok = False

    # Hermetic corpus-shape probe: a real temp doc through the file path.
    tmp = Path(tempfile.mkdtemp())
    try:
        doc = tmp / "module_99.md"
        doc.write_text(
            "### `vm_carbon_stock`\n"
            "- **Declared in**: Module 52 (declarations.gms:34).\n"  # wrong -> flag
            "`vm_prod` is declared in Module 17.\n"                  # correct -> no flag
        )
        fnd = scan_doc(doc.read_text(), doc.name, producers, consumers)
        # exactly one finding (the Module 52 declared-in line), var vm_carbon_stock
        if len(fnd) == 1 and fnd[0]["var"] == "vm_carbon_stock" and fnd[0]["claimed"] == 52:
            print("  SELF-TEST PASS [tempfile-mixed]")
        else:
            print(f"  SELF-TEST FAIL [tempfile-mixed]: got {fnd}")
            ok = False
    finally:
        for p in tmp.iterdir():
            p.unlink()
        tmp.rmdir()

    # --- suppression path (R57): this was DEAD to the self-test, which is how the
    # "entries"-vs-"allowlist" key bug survived. Assert BOTH schema shapes parse.
    row = [{"check": CHECK_NAME, "file": "modules/module_99.md", "key": "vm_x"}]
    for label, payload, expect in [
        ("allowlist-key-schema", {"allowlist": row}, {("modules/module_99.md", "vm_x")}),
        ("entries-key-schema", {"entries": row}, {("modules/module_99.md", "vm_x")}),
        ("bare-list-schema", row, {("modules/module_99.md", "vm_x")}),
        ("other-check-rows-ignored",
         {"allowlist": [{"check": "check_other", "file": "f", "key": "k"}]}, set()),
    ]:
        got = parse_allowlist(payload)
        if got == expect:
            print(f"  SELF-TEST PASS [{label}]")
        else:
            print(f"  SELF-TEST FAIL [{label}]: expected {expect}, got {got}")
            ok = False

    # The real file must be parseable by THIS checker's reader -- a synthetic fixture
    # alone cannot catch a schema drift in the actual allowlist (that is precisely the
    # gap that hid the key bug: the fixture never used the real file's shape).
    if ALLOWLIST_PATH.exists():
        try:
            real = json.loads(ALLOWLIST_PATH.read_text())
            rows = real if isinstance(real, list) else (
                real.get("allowlist") or real.get("entries") or [])
            if rows:
                print("  SELF-TEST PASS [real-allowlist-file-has-parseable-rows]")
            else:
                print("  SELF-TEST FAIL [real-allowlist-file-has-parseable-rows]: "
                      "0 rows -- schema drift would silently empty every suppression list")
                ok = False
        except (ValueError, OSError) as e:
            print(f"  SELF-TEST FAIL [real-allowlist-file-has-parseable-rows]: {e}")
            ok = False

    if ok:
        print(f"{CHECK_NAME} self-test: PASS")
        print(f"SELFTEST_OK {CHECK_NAME}")
        return 0
    print(f"{CHECK_NAME} self-test: FAIL")
    return 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(main())
