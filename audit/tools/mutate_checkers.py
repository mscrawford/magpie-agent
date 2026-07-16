#!/usr/bin/env python3
"""
W0a -- mutation-test the magpie-agent checkers (audit round R57).

QUESTION: R55's headline is "every mechanized class = 0.00 residual". That is only
meaningful if the checkers actually ASSERT. The known SELFTEST_OK contract proves a
check RAN, not that its assertions ran (real bug: check_attribution_omissions reported
"19 cases / PASS" while only 16 assertions executed).

METHOD: seed AST mutations into each checker's logic, run its --self-test, and assert
the self-test goes RED. A mutation that SURVIVES (self-test still green) means no
assertion covers that code path.

Killed   = self-test exit != 0, OR the SELFTEST_OK sentinel is absent.
Survived = self-test exit 0 AND sentinel present, with mutated logic. <-- the finding.

The self_test() function body is EXCLUDED from mutation: mutating the test is not
testing the test.

Survivors need triage by location:
  HIGH  -- a detection predicate (an inert assertion; the class this round hunts), OR
           a function that emits the user-visible VERDICT. Per feedback_test_the_testers,
           a real case had report() printing "VERDICT: SAFE TO SHARE" with ZERO coverage:
           the verdict line is exactly what a human reads, so uncovered verdict logic is
           NOT a formatting nitpick. Do not downgrade these.
  LOW   -- pure output formatting / arg parsing with no verdict semantics.
Equivalent mutants (semantically identical, unkillable) also land in survivors; triage
must separate them from genuine coverage gaps rather than inflate the rate.

Usage:
  python3 audit/tools/mutate_checkers.py --self-check          # positive/negative control pair (RUN FIRST)
  python3 audit/tools/mutate_checkers.py --scripts-dir DIR     # mutate all rostered checkers
  python3 audit/tools/mutate_checkers.py --scripts-dir DIR --only check_scaling
"""
import argparse
import ast
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROSTER = [
    "check_gams_citations_impl", "check_default_realizations", "check_gams_variables",
    "check_doc_var_existence", "check_scaling", "check_consumer_attribution",
    "check_hedged_claims", "check_module_realizations", "probe_dedup_check",
    "check_gams_equations", "check_gams_realizations", "check_no_bare_cites",
    "check_param_defaults", "check_renames", "check_set_members",
    "check_intra_doc_contradiction", "check_role_attribution",
    "check_attribution_tables", "check_attribution_prose",
    "check_attribution_omissions", "check_dependent_counts",
    "gams_slices", "check_dependent_direction", "check_bindability",
]

CMP_SWAP = {
    ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    ast.Lt: ast.GtE, ast.GtE: ast.Lt,
    ast.Gt: ast.LtE, ast.LtE: ast.Gt,
    ast.In: ast.NotIn, ast.NotIn: ast.In,
    ast.Is: ast.IsNot, ast.IsNot: ast.Is,
}


class SiteFinder(ast.NodeVisitor):
    """Collect mutable sites, tagged with the enclosing function (for triage)."""

    def __init__(self, skip_ranges):
        self.sites = []          # (node_id, kind, lineno, func)
        self.skip = skip_ranges  # line ranges to exclude (self_test bodies)
        self.func_stack = []

    def _skipped(self, node):
        ln = getattr(node, "lineno", None)
        if ln is None:
            return True
        return any(lo <= ln <= hi for lo, hi in self.skip)

    def _func(self):
        return self.func_stack[-1] if self.func_stack else "<module>"

    def visit_FunctionDef(self, node):
        self.func_stack.append(node.name)
        self.generic_visit(node)
        self.func_stack.pop()

    def visit_Compare(self, node):
        if not self._skipped(node):
            for i, op in enumerate(node.ops):
                if type(op) in CMP_SWAP:
                    self.sites.append((id(node), f"cmp{i}", node.lineno, self._func()))
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        if not self._skipped(node):
            self.sites.append((id(node), "boolop", node.lineno, self._func()))
        self.generic_visit(node)

    def visit_UnaryOp(self, node):
        if not self._skipped(node) and isinstance(node.op, ast.Not):
            self.sites.append((id(node), "not", node.lineno, self._func()))
        self.generic_visit(node)

    def visit_Constant(self, node):
        if not self._skipped(node) and isinstance(node.value, bool):
            self.sites.append((id(node), "bool", node.lineno, self._func()))
        self.generic_visit(node)


class Mutator(ast.NodeTransformer):
    """Apply exactly ONE mutation, identified by (node_id, kind)."""

    def __init__(self, target_id, kind):
        self.target_id = target_id
        self.kind = kind
        self.applied = False

    def visit_Compare(self, node):
        self.generic_visit(node)
        if id(node) == self.target_id and self.kind.startswith("cmp"):
            i = int(self.kind[3:])
            new = copy.deepcopy(node)
            new.ops[i] = CMP_SWAP[type(node.ops[i])]()
            self.applied = True
            return new
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if id(node) == self.target_id and self.kind == "boolop":
            new = copy.deepcopy(node)
            new.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
            self.applied = True
            return new
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if id(node) == self.target_id and self.kind == "not":
            self.applied = True
            return node.operand          # strip the `not`
        return node

    def visit_Constant(self, node):
        if id(node) == self.target_id and self.kind == "bool":
            self.applied = True
            return ast.Constant(value=not node.value)
        return node


def selftest_ranges(tree):
    """Line ranges of self_test() bodies -- excluded from mutation."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and "self_test" in node.name:
            out.append((node.lineno, node.end_lineno))
    return out


def run_selftest(script_path: Path, name: str):
    try:
        p = subprocess.run([sys.executable, str(script_path), "--self-test"],
                           capture_output=True, text=True, timeout=60,
                           cwd=str(script_path.parent))
    except subprocess.TimeoutExpired:
        return False, "timeout"
    green = p.returncode == 0 and f"SELFTEST_OK {name}" in p.stdout
    return green, f"rc={p.returncode}"


def mutate_file(src: Path, name: str, workdir: Path, limit=None):
    source = src.read_text()
    tree = ast.parse(source)
    skip = selftest_ranges(tree)
    finder = SiteFinder(skip)
    finder.visit(tree)
    sites = finder.sites
    if limit:
        sites = sites[:limit]

    results = []
    target = workdir / f"{name}.py"
    for node_id, kind, lineno, func in sites:
        t2 = ast.parse(source)                 # fresh tree: node ids must match
        f2 = SiteFinder(skip)
        f2.visit(t2)
        match = [s for s in f2.sites if (s[1], s[2], s[3]) == (kind, lineno, func)]
        if not match:
            continue
        m = Mutator(match[0][0], kind)
        t2 = m.visit(t2)
        if not m.applied:
            continue
        ast.fix_missing_locations(t2)
        try:
            code = ast.unparse(t2)
        except Exception as e:
            results.append(dict(line=lineno, kind=kind, func=func,
                                status="unparse_error", detail=str(e)[:80]))
            continue
        orig = target.read_text()
        try:
            target.write_text(code)
            green, detail = run_selftest(target, name)
        finally:
            target.write_text(orig)            # always restore
        results.append(dict(line=lineno, kind=kind, func=func,
                            status="SURVIVED" if green else "killed", detail=detail))
    return results


# ---------------------------------------------------------------- self-check
CONTROL_SRC = '''\
import sys, re

def detect_covered(text):
    """Self-test asserts on this. A mutation here MUST be killed."""
    return len(text) > 3

def detect_dead(text):
    """Nothing calls this. A mutation here MUST survive."""
    return len(text) > 3

def self_test():
    if detect_covered("abcd") != True:
        return 1
    if detect_covered("ab") != False:
        return 1
    print("SELFTEST_OK control_mod")
    return 0

if "--self-test" in sys.argv:
    sys.exit(self_test())
'''


def self_check(tmp: Path):
    """Positive/negative control PAIR. The harness must prove it can do both:
    kill a mutation in covered logic, and report a survivor in dead logic.
    A harness that cannot detect survivors gives a false green exactly like
    the bug it hunts."""
    p = tmp / "control_mod.py"
    p.write_text(CONTROL_SRC)
    green, _ = run_selftest(p, "control_mod")
    if not green:
        print("SELF-CHECK FAIL: unmutated control is not green")
        return 1
    res = mutate_file(p, "control_mod", tmp)
    cov = [r for r in res if r["func"] == "detect_covered"]
    dead = [r for r in res if r["func"] == "detect_dead"]
    ok = True
    if not cov or not all(r["status"] == "killed" for r in cov):
        print(f"SELF-CHECK FAIL: covered-logic mutants not killed: {cov}")
        ok = False
    if not dead or not all(r["status"] == "SURVIVED" for r in dead):
        print(f"SELF-CHECK FAIL: dead-logic mutants not reported as survivors: {dead}")
        ok = False
    if ok:
        print(f"SELF-CHECK PASS: {len(cov)} covered mutants killed, "
              f"{len(dead)} dead mutants survived (harness detects BOTH outcomes)")
        print("SELFCHECK_OK mutate_checkers")
        return 0
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scripts-dir")
    ap.add_argument("--only")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as td:
        if a.self_check:
            sys.exit(self_check(Path(td)))

    src_dir = Path(a.scripts_dir).resolve()
    # SAFETY: never mutate the caller's tree. mutate_file() writes each mutant to disk
    # and restores in a `finally`, but a hard kill (SIGKILL, OOM) between write and
    # restore would strand a MUTATED checker in the working tree -- a validator that
    # silently reports wrong results is the exact failure class this tool exists to
    # find. Always work on a throwaway copy instead; the tempdir is auto-removed.
    tmp_root = tempfile.mkdtemp(prefix="mutate_checkers_")
    sd = Path(tmp_root) / "scripts"
    shutil.copytree(src_dir, sd)
    print(f"mutating a COPY at {sd} (source tree untouched)\n")

    names = [a.only] if a.only else ROSTER
    allres, summary = {}, []
    for name in names:
        src = sd / f"{name}.py"
        if not src.exists():
            print(f"  {name}: MISSING", file=sys.stderr)
            continue
        green, _ = run_selftest(src, name)
        if not green:
            print(f"  {name}: BASELINE NOT GREEN -- skipping", file=sys.stderr)
            continue
        res = mutate_file(src, name, sd, limit=a.limit)
        allres[name] = res
        surv = [r for r in res if r["status"] == "SURVIVED"]
        tot = len([r for r in res if r["status"] in ("SURVIVED", "killed")])
        rate = (len(surv) / tot * 100) if tot else 0.0
        summary.append((name, tot, len(surv), rate))
        print(f"  {name}: {tot} mutants, {len(surv)} survived ({rate:.1f}%)", flush=True)

    print("\n=== W0a MUTATION SUMMARY ===")
    print(f"{'checker':<34}{'mutants':>9}{'survived':>10}{'survival%':>11}")
    tt = ss = 0
    for name, tot, ns, rate in sorted(summary, key=lambda x: -x[3]):
        print(f"{name:<34}{tot:>9}{ns:>10}{rate:>10.1f}%")
        tt += tot; ss += ns
    overall = (ss / tt * 100) if tt else 0.0
    print(f"{'TOTAL':<34}{tt:>9}{ss:>10}{overall:>10.1f}%")
    print(f"\nMUTATION_RESULT: mutants={tt} survived={ss} survival={overall:.1f}%")
    print("HALT THRESHOLD: >20% survival => round becomes 'fix the instruments'")
    shutil.rmtree(tmp_root, ignore_errors=True)
    if a.json:
        Path(a.json).write_text(json.dumps(allres, indent=1))
        print(f"detail -> {a.json}")


if __name__ == "__main__":
    main()
