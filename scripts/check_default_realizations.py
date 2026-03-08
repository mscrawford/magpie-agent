#!/usr/bin/env python3
"""Check 18: Cross-reference default realization labels in docs against config/default.cfg.

Detects the "Interesting Over Default" antipattern where AI docs label a non-default
realization as "(default)". This was the root cause of doc errors in M37, M38, M80
across validation rounds R14-R15.

Usage: python3 scripts/check_default_realizations.py [--fix]
  --fix: Print suggested fixes (does not modify files)

Exit codes:
  0: All checks pass
  1: Mismatches found
"""

import os
import re
import sys

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


def check_doc_default_labels(module_num, module_name, actual_default):
    """Check a module doc for "(default)" labels and compare against actual default."""
    doc_path = os.path.join(DOCS_DIR, f"module_{module_num}.md")
    if not os.path.isfile(doc_path):
        return None  # No doc for this module

    mismatches = []
    with open(doc_path, "r") as f:
        lines = f.readlines()

    # Check if the actual default realization is available in the module dir
    module_dir = os.path.join(MODULES_DIR, f"{module_num}_{module_name}")
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
        default_real_match = re.search(r"[Dd]efault\s+[Rr]ealization[:\s]*`?(\w+)`?", line)
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


def main():
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
