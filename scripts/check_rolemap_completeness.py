#!/usr/bin/env python3
"""Role-map COMPLETENESS guard -- the missing control on the ground-truth anchor.

WHY THIS EXISTS (R57 / W0a):
  build_role_map() in check_attribution_omissions.py is the code-derived ground truth
  for Checks 34/35/36 -- the whole R56 mechanization arc. W0a measured that it has
  ZERO self-test coverage: replace its body with `raise` and every self-test in the
  battery still reports green. Its only validation was one-time manual historical
  replays, which are not automated and not gated. So a silent regression in the map
  builder would surface as "0 findings" -- indistinguishable from a clean corpus.

  This guard is that missing control. It independently enumerates interface variables
  from the GAMS tree and asserts the role map contains every (module, variable)
  reference it finds.

DECORRELATION (the load-bearing design constraint):
  This checker MUST NOT import CROSS_IFACE_RE, _strip_comments, or _classify_statement
  from the module under test -- it would inherit the very bug it exists to catch. It
  uses its own comment-stripper, its own tokenizer, and no ';'-splitting. Different
  reader, different anchor. See template_multi_agent_audit: "an empirical re-derivation
  lens must use a DIFFERENT reader than the pipeline does."

FOUND ON FIRST RUN -- a live positive control, not a fixture (R57):
  vm_AEI (declared in modules/41_area_equipped_for_irrigation/*/declarations.gms,
  consumed by modules/30_croparea/detail_apr24/equations.gms:82) was absent from the
  role map ENTIRELY, because CROSS_IFACE_RE required a lowercase letter after the
  prefix and vm_AEI is uppercase. Five-plus doc sites make vm_AEI attribution claims
  that Checks 34/35/36 silently skipped and reported clean.

SCOPE / LIMITS (do not overstate this guard):
  - It is a SUPERSET test. It catches UNDER-population -- a reference present in the
    code that the role map lacks. That is the direction that hides omissions and
    prints a false "0 findings".
  - It does NOT verify role CORRECTNESS. A variable recorded under POPULATE when it
    should be READ passes this guard. Role-correctness remains unmechanized.
  - Over-population (a role-map entry this scan cannot see) is reported as advisory
    context only, since the role map legitimately resolves forms this scan does not.

Usage:
  python3 scripts/check_rolemap_completeness.py              # scan (advisory)
  python3 scripts/check_rolemap_completeness.py --strict     # exit 1 if drops found
  python3 scripts/check_rolemap_completeness.py --self-test  # positive control
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

from check_attribution_omissions import build_role_map  # noqa: E402  (module under test)
from check_gams_variables import MAGPIE_DIR  # noqa: E402

CHECK_NAME = "check_rolemap_completeness"

# --- OWN reader. Deliberately NOT imported from the module under test. ---------
# Interface prefixes per MANDATE 18 + fm_ inputs. Case-INSENSITIVE after the
# prefix on purpose: the bug this guard caught was a [a-z] gate dropping vm_AEI.
IFACE_RE = re.compile(r"\b((?:vm|pm|im|pcm|fm)_[A-Za-z][A-Za-z0-9_]*)\b")


def strip_comments_own(text: str) -> str:
    """GAMS comments: column-1 '*' lines and $ontext/$offtext blocks.

    Independent reimplementation -- see DECORRELATION above.
    """
    out: list[str] = []
    in_block = False
    for line in text.split("\n"):
        low = line.strip().lower()
        if low.startswith("$ontext"):
            in_block = True
            continue
        if low.startswith("$offtext"):
            in_block = False
            continue
        if in_block or line[:1] == "*":
            continue
        out.append(line)
    return "\n".join(out)


def scan_interface_refs(modules_root: Path) -> dict[str, set[str]]:
    """{var: {module_number, ...}} for every interface var referenced in non-comment
    GAMS text. A superset of any role map built from the same tree."""
    refs: dict[str, set[str]] = defaultdict(set)
    if not modules_root.is_dir():
        return refs
    for mdir in sorted(modules_root.iterdir()):
        if not mdir.is_dir():
            continue
        mnum = mdir.name.split("_", 1)[0]
        if not mnum.isdigit():
            continue
        for path in mdir.rglob("*.gms"):
            try:
                code = strip_comments_own(path.read_text(errors="replace"))
            except OSError:
                continue
            for var in set(IFACE_RE.findall(code)):
                refs[var].add(mnum)
    return refs


def role_union(role: dict) -> dict[str, set[str]]:
    """{var: {modnum,...}} union of every role the map records for that var."""
    return {v: set(mods) for v, mods in ((v, m.keys()) for v, m in role.items())}


def compare(scanned: dict[str, set[str]], role_u: dict[str, set[str]]) -> dict:
    """Pure detection logic. Returns dropped vars + missing (module,var) pairs."""
    dropped, missing_pairs, over = [], [], []
    for var, mods in sorted(scanned.items()):
        if var not in role_u:
            dropped.append({"var": var, "modules": sorted(mods)})
            continue
        gap = mods - role_u[var]
        if gap:
            missing_pairs.append({"var": var, "modules": sorted(gap),
                                  "rolemap_has": sorted(role_u[var])})
    for var, mods in sorted(role_u.items()):
        extra = mods - scanned.get(var, set())
        if extra:
            over.append({"var": var, "modules": sorted(extra)})
    return {"dropped": dropped, "missing_pairs": missing_pairs, "over": over,
            "scanned_vars": len(scanned), "rolemap_vars": len(role_u)}


def run_scan(modules_root: Path) -> dict:
    role, _ = build_role_map()
    return compare(scan_interface_refs(modules_root), role_union(role))


def verdict(n_drop: int, n_pair: int) -> tuple[str, bool]:
    """Return (verdict_line, is_incomplete).

    Extracted from main() deliberately: per feedback_test_the_testers, a self-test
    that never drives the function producing the user-visible verdict leaves the one
    line a human actually reads with zero coverage -- a real audit found
    "VERDICT: SAFE TO SHARE" untested for exactly this reason. Keeping the decision
    pure makes it directly assertable.
    """
    if n_drop or n_pair:
        return ("VERDICT: role map is INCOMPLETE -- downstream Checks 34/35/36 are "
                "silently blind to the above.", True)
    return ("VERDICT: role map is complete w.r.t. an independent scan "
            "(under-population direction only; role correctness NOT checked).", False)


# --------------------------------------------------------------- self-test ----
_FIXTURE = {
    "modules/41_irrig/static/declarations.gms":
        " vm_UPPER(j)      Area equipped for irrigation (mio. ha)\n"
        " vm_lower(j)      Something lowercase (mio. ha)\n",
    "modules/41_irrig/static/equations.gms":
        "q41_a(j2) .. sum(kcr, vm_area(j2,kcr)) =l= vm_UPPER(j2);\n"
        "q41_b(j2) .. x(j2) =l= vm_lower(j2);\n",
    "modules/30_crop/detail/equations.gms":
        "q30_a(j2) .. y(j2) =e= vm_UPPER(j2) * 2 + vm_lower(j2);\n",
    # comment-only mention: must NOT be scanned as a reference.
    # vm_after sits AFTER $offtext on purpose: it pins block-comment delimiter
    # tracking, so a desync (the `others` set-fabrication bug class) is caught.
    "modules/52_carbon/normal/equations.gms":
        "*' this line mentions vm_UPPER(j) in a comment only\n"
        "$ontext\n vm_lower(j) inside a block comment\n$offtext\n"
        "q52_a(j2) .. z(j2) =e= vm_after(j2);\n",
}


def _write_fixture(root: Path) -> None:
    for rel, body in _FIXTURE.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)


def _scan_only() -> int:
    """Internal: drive the FULL composition over MAGPIE_DIR and emit JSON.

    Routes through run_scan() (not build_role_map directly) so the subprocess
    exercises run_scan + role_union + compare end-to-end against a real tree --
    otherwise the composition layer would be dead to the self-test, which is the
    very defect W0a found in the existing battery.
    """
    scanned = scan_interface_refs(MAGPIE_DIR / "modules")
    print(json.dumps({
        "scanned": {k: sorted(v) for k, v in scanned.items()},
        "result": run_scan(MAGPIE_DIR / "modules"),
    }))
    return 0


EXPECTED_ASSERTIONS = 18


def self_test() -> int:
    """Positive control.

    NOTE the design: this self-test drives the REAL scanner over a REAL (synthetic)
    tree on disk via a subprocess with MAGPIE_DIR overridden -- it does NOT stub the
    ground-truth extractor. Stubbing the extractor is precisely the defect W0a found
    in the existing battery, and this guard must not reproduce it.
    """
    checks: list[tuple[str, bool]] = []

    def check(name: str, cond: bool) -> None:
        checks.append((name, bool(cond)))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write_fixture(root)

        env = dict(os.environ, MAGPIE_DIR=str(root))
        p = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--_scan-only"],
                           capture_output=True, text=True, env=env, timeout=120)
        if p.returncode != 0:
            print(f"self-test: FAIL subprocess rc={p.returncode}\n{p.stderr[:400]}")
            return 1
        data = json.loads(p.stdout)
        scanned = {k: set(v) for k, v in data["scanned"].items()}
        result = data["result"]

        # --- the SCANNER (own reader) is exercised against real files on disk -----
        check("scanner finds uppercase iface var", "vm_UPPER" in scanned)
        check("scanner attributes vm_UPPER to both 30 and 41",
              scanned.get("vm_UPPER") == {"30", "41"})
        check("scanner finds lowercase iface var", "vm_lower" in scanned)
        check("scanner ignores comment-only mention (M52 absent for vm_UPPER)",
              "52" not in scanned.get("vm_UPPER", set()))
        check("scanner ignores $ontext block (M52 absent for vm_lower)",
              "52" not in scanned.get("vm_lower", set()))
        check("scanner RESUMES after $offtext (delimiter tracking not desynced)",
              scanned.get("vm_after") == {"52"})

        # --- the COMPOSITION (run_scan -> role_union -> compare) end-to-end -------
        # Assertions deliberately chosen to be STABLE across the CROSS_IFACE_RE fix:
        # they must not encode whether vm_UPPER is currently dropped, or this
        # self-test would flip red the moment the bug it documents is fixed.
        check("run_scan returns the full result shape",
              all(k in result for k in
                  ("dropped", "missing_pairs", "over", "scanned_vars", "rolemap_vars")))
        check("run_scan actually scanned the tree (non-zero denominator)",
              result["scanned_vars"] >= 2)
        check("run_scan/role_union resolve a lowercase var as present (not dropped)",
              "vm_lower" not in [d["var"] for d in result["dropped"]])
        check("run_scan reports no missing pair for the lowercase var",
              "vm_lower" not in [m["var"] for m in result["missing_pairs"]])

    # --- the COMPARISON logic, on synthetic inputs ----------------------------
    r = compare({"vm_x": {"10", "30"}}, {})
    check("dropped var is flagged", len(r["dropped"]) == 1 and r["dropped"][0]["var"] == "vm_x")

    r = compare({"vm_x": {"10", "30"}}, {"vm_x": {"10", "30"}})
    check("complete map is clean", not r["dropped"] and not r["missing_pairs"])

    r = compare({"vm_x": {"10", "30"}}, {"vm_x": {"10"}})
    check("missing (module,var) pair is flagged",
          len(r["missing_pairs"]) == 1 and r["missing_pairs"][0]["modules"] == ["30"])

    r = compare({"vm_x": {"10"}}, {"vm_x": {"10", "99"}})
    check("over-population is reported separately, not as a drop",
          not r["dropped"] and not r["missing_pairs"] and len(r["over"]) == 1)

    # --- the VERDICT a human reads (test the sentence, not just the internals) --
    line, bad = verdict(0, 0)
    check("verdict(0,0) reports complete", bad is False and "complete" in line)
    check("verdict(0,0) does NOT claim role correctness", "role correctness NOT checked" in line)
    line, bad = verdict(1, 0)
    check("verdict(drop) reports INCOMPLETE", bad is True and "INCOMPLETE" in line)
    line, bad = verdict(0, 1)
    check("verdict(missing_pair) reports INCOMPLETE", bad is True and "INCOMPLETE" in line)

    # Guard against inert assertions: an appended case that never runs is the exact
    # silent-green this round exists to kill (feedback_selftest_assertion_count).
    if len(checks) != EXPECTED_ASSERTIONS:
        print(f"self-test: FAIL expected {EXPECTED_ASSERTIONS} assertions, ran {len(checks)}")
        return 1

    failed = [n for n, ok in checks if not ok]
    for name, ok in checks:
        print(f"  SELF-TEST {'PASS' if ok else 'FAIL'} [{name}]")
    if failed:
        print(f"self-test: FAIL ({len(failed)}/{len(checks)})")
        return 1
    print(f"self-test: PASS ({len(checks)} assertions)")
    print(f"SELFTEST_OK {CHECK_NAME}")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if "--_scan-only" in sys.argv:
        return _scan_only()

    res = run_scan(MAGPIE_DIR / "modules")
    n_drop = len(res["dropped"])
    n_pair = len(res["missing_pairs"])

    for d in res["dropped"]:
        print(f"DROPPED  {d['var']}: referenced by modules {','.join(d['modules'])} "
              f"but ABSENT from the role map -> every attribution claim about it is "
              f"unverifiable by Checks 34/35/36")
    for m in res["missing_pairs"]:
        print(f"MISSING  {m['var']}: modules {','.join(m['modules'])} reference it but "
              f"the role map has only {','.join(m['rolemap_has'])}")

    print(f"\n{CHECK_NAME}: SUMMARY scanned_vars={res['scanned_vars']} "
          f"rolemap_vars={res['rolemap_vars']} dropped={n_drop} missing_pairs={n_pair} "
          f"over={len(res['over'])}")
    line, incomplete = verdict(n_drop, n_pair)
    print(line)

    if "--strict" in sys.argv and incomplete:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
