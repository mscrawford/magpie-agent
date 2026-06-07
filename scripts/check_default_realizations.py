#!/usr/bin/env python3
"""Check 18: Cross-reference default realization labels in docs against config/default.cfg.

Detects the "Interesting Over Default" antipattern where AI docs label a non-default
realization as "(default)". This was the root cause of doc errors in M37, M38, M80
across validation rounds R14-R15.

Usage: python3 scripts/check_default_realizations.py [--fix] [--self-test]
  --fix: Print suggested fixes (does not modify files)
  --self-test: Run positive/clean controls on synthetic fixtures (exits 1 on failure)

Exit codes:
  0: All checks pass (or --self-test passed)
  1: Mismatches found (or --self-test failed)
"""

import os
import re
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_DIR = os.path.dirname(SCRIPT_DIR)
MAGPIE_DIR = os.path.dirname(AGENT_DIR)

DEFAULT_CFG = os.path.join(MAGPIE_DIR, "config", "default.cfg")
MODULES_DIR = os.path.join(MAGPIE_DIR, "modules")
DOCS_DIR = os.path.join(AGENT_DIR, "modules")


def get_module_name_to_number():
    """Build mapping from module name to number using directory listing."""
    mapping = {}
    if not os.path.isdir(MODULES_DIR):
        return mapping
    for entry in os.listdir(MODULES_DIR):
        match = re.match(r"^(\d+)_(.+)$", entry)
        if match:
            num = match.group(1)
            name = match.group(2)
            mapping[name] = num
    return mapping


def get_default_realizations():
    """Parse config/default.cfg for module realization settings."""
    defaults = {}
    if not os.path.isfile(DEFAULT_CFG):
        print(f"  Warning: {DEFAULT_CFG} not found", file=sys.stderr)
        return defaults

    # Match lines like: cfg$gms$land <- "landmatrix_dec18"
    pattern = re.compile(r'^cfg\$gms\$(\w+)\s*<-\s*"([^"]+)"')
    with open(DEFAULT_CFG, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                continue
            m = pattern.match(line)
            if m:
                key = m.group(1)
                value = m.group(2)
                defaults[key] = value
    return defaults


def check_doc_default_labels(module_num, module_name, actual_default,
                              docs_dir=None, gams_modules_dir=None):
    """Check a module doc for "(default)" labels and compare against actual default.

    docs_dir / gams_modules_dir: override the global DOCS_DIR / MODULES_DIR.
    Used only by --self-test; real-tree behaviour is unchanged when both are None.
    """
    _docs = docs_dir if docs_dir is not None else DOCS_DIR
    _mods = gams_modules_dir if gams_modules_dir is not None else MODULES_DIR

    doc_path = os.path.join(_docs, f"module_{module_num}.md")
    if not os.path.isfile(doc_path):
        return None  # No doc for this module

    mismatches = []
    with open(doc_path, "r") as f:
        lines = f.readlines()

    # Check if the actual default realization is available in the module dir
    module_dir = os.path.join(_mods, f"{module_num}_{module_name}")
    if os.path.isdir(module_dir):
        available_realizations = [
            d for d in os.listdir(module_dir)
            if os.path.isdir(os.path.join(module_dir, d))
            and not d.startswith(".")
            and d != "input"
            and d != "__pycache__"
        ]
    else:
        available_realizations = []

    for i, line in enumerate(lines, 1):
        # Skip lines about config/default.cfg or general "default" discussion
        if re.search(r"default\.cfg|config/default|by default|default behavior|default value|default state|default setting", line, re.IGNORECASE):
            continue

        # Look for pattern: `realization_name` (default) or `realization_name` **(default)**
        # This ensures "(default)" is directly associated with a specific realization
        for match in re.finditer(r"`(\w+)`\s*\((?:default|Default)\)", line):
            claimed = match.group(1)
            if claimed in available_realizations and claimed != actual_default:
                mismatches.append({
                    "line": i,
                    "text": line.rstrip(),
                    "claimed_default": claimed,
                    "actual_default": actual_default,
                })

        # Also check: **realization_name** (default)
        for match in re.finditer(r"\*\*(\w+)\*\*\s*\((?:default|Default)\)", line):
            claimed = match.group(1)
            if claimed in available_realizations and claimed != actual_default:
                mismatches.append({
                    "line": i,
                    "text": line.rstrip(),
                    "claimed_default": claimed,
                    "actual_default": actual_default,
                })

        # Check header patterns like "Realization: realname (default)"
        # or "Default realization: realname" where realname is NOT the actual default
        # R4 fix (2026-05-24): allow optional bold wrappers around 'Default Realization'
        # AND around the captured name. Previously the regex required `[:\s]*` between
        # 'Realization' and the colon, which failed for the canonical `**Default
        # Realization**: \`name\`` format used by ALL 46 module-doc headers — making
        # Check 18's Pattern C effectively dormant.
        default_real_match = re.search(
            r"\*{0,2}[Dd]efault\s+[Rr]ealization\*{0,2}\s*:?\s*\*{0,2}\s*`?(\w+)`?",
            line,
        )
        if default_real_match:
            claimed = default_real_match.group(1)
            if claimed in available_realizations and claimed != actual_default:
                mismatches.append({
                    "line": i,
                    "text": line.rstrip(),
                    "claimed_default": claimed,
                    "actual_default": actual_default,
                })

    return mismatches


def self_test():
    """Positive and clean controls on synthetic temp-tree fixtures.

    Builds an isolated tempdir — does NOT touch the real tree.
    Positive control: doc claims realB is default, config says realA → must FLAG.
    Clean control:   doc claims realA is default, config says realA → must PASS.
    Exits 0 iff both assertions hold; exits 1 if either fails.
    """
    import shutil

    tmp = tempfile.mkdtemp(prefix="check18_selftest_")
    ok = True
    try:
        # --- Fixture layout ---
        #   <tmp>/config/default.cfg          <- realA is the default
        #   <tmp>/modules/99_testmod/realA/   <- realization dirs (both present)
        #   <tmp>/modules/99_testmod/realB/
        #   <tmp>/docs/module_99.md           <- the AI doc under test (two variants)

        cfg_dir = os.path.join(tmp, "config")
        gams_mod_dir = os.path.join(tmp, "modules", "99_testmod")
        docs_dir = os.path.join(tmp, "docs")

        os.makedirs(cfg_dir)
        os.makedirs(os.path.join(gams_mod_dir, "realA"))
        os.makedirs(os.path.join(gams_mod_dir, "realB"))
        os.makedirs(docs_dir)

        cfg_path = os.path.join(cfg_dir, "default.cfg")
        with open(cfg_path, "w") as f:
            f.write('cfg$gms$testmod <- "realA"\n')

        # ---- assertion 1: positive control — doc claims realB (wrong) ----
        doc_positive = os.path.join(docs_dir, "module_99.md")
        with open(doc_positive, "w") as f:
            f.write("# Module 99 testmod\n")
            f.write("**Default Realization**: `realB`\n")

        gams_modules_dir = os.path.join(tmp, "modules")
        mismatches = check_doc_default_labels(
            "99", "testmod", "realA",
            docs_dir=docs_dir,
            gams_modules_dir=gams_modules_dir,
        )
        if mismatches:
            print("  SELF-TEST PASS: positive control flagged mismatch"
                  f" (claimed realB, actual realA) on line {mismatches[0]['line']}")
        else:
            print("  SELF-TEST FAIL: positive control did NOT flag doc claiming"
                  " realB as default (actual default is realA)")
            ok = False

        # ---- assertion 2: clean control — doc claims realA (correct) ----
        with open(doc_positive, "w") as f:
            f.write("# Module 99 testmod\n")
            f.write("**Default Realization**: `realA`\n")

        mismatches_clean = check_doc_default_labels(
            "99", "testmod", "realA",
            docs_dir=docs_dir,
            gams_modules_dir=gams_modules_dir,
        )
        if not mismatches_clean:
            print("  SELF-TEST PASS: clean control produced no mismatches"
                  " (doc correctly states realA)")
        else:
            print("  SELF-TEST FAIL: clean control wrongly flagged a correct doc"
                  f" ({mismatches_clean})")
            ok = False

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("check_default_realizations self-test: PASS")
        print("SELFTEST_OK check_default_realizations")
        sys.exit(0)
    else:
        print("check_default_realizations self-test: FAIL")
        sys.exit(1)


def main():
    if "--self-test" in sys.argv:
        self_test()  # self_test() calls sys.exit() internally

    show_fix = "--fix" in sys.argv

    name_to_num = get_module_name_to_number()
    defaults = get_default_realizations()

    if not name_to_num:
        print("  Error: Could not find MAgPIE modules directory")
        sys.exit(1)

    if not defaults:
        print("  Error: Could not parse default.cfg")
        sys.exit(1)

    total_checked = 0
    total_mismatches = 0
    all_mismatches = []

    for module_name, module_num in sorted(name_to_num.items(), key=lambda x: int(x[1])):
        if module_name not in defaults:
            continue

        actual_default = defaults[module_name]
        mismatches = check_doc_default_labels(module_num, module_name, actual_default)

        if mismatches is None:
            continue  # No doc file

        total_checked += 1

        if mismatches:
            total_mismatches += len(mismatches)
            for m in mismatches:
                all_mismatches.append({
                    "module": f"M{module_num} ({module_name})",
                    **m,
                })

    # Output results
    if all_mismatches:
        print(f"  Found {total_mismatches} default realization mismatch(es) in {total_checked} modules:")
        for m in all_mismatches:
            print(f"    {m['module']}: line {m['line']} claims `{m['claimed_default']}` is default, "
                  f"but config/default.cfg says `{m['actual_default']}`")
            if show_fix:
                print(f"      Fix: Replace `{m['claimed_default']}` with `{m['actual_default']}` as default")
                print(f"      Line: {m['text']}")
        sys.exit(1)
    else:
        print(f"  {total_checked} modules checked: all default realization labels match config/default.cfg")
        sys.exit(0)


if __name__ == "__main__":
    main()
