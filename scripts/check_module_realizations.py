#!/usr/bin/env python3
"""Realization-validity check for module docs.

For each `modules/module_XX.md`:
1. Extract the realization claimed in the header (e.g., `# Module 14: Yields (managementcalib_aug19)`)
   AND any realization cited in the `Verified Against:` footer
2. Look up the actual default realization from `../config/default.cfg`
3. Verify:
   (a) the directory exists (`../modules/XX_name/<realization>/`)
   (b) the header-claimed realization matches the default (WARN otherwise)
   (c) the footer-cited realization matches the default AND exists (ERROR otherwise)

Closes R1 audit Cluster 1 (Module 18 wrong-realization CRITICAL + 13/46 footer fabrications).

Exit code: 0 if all clean, 1 if any ERROR finding, 2 if only WARN findings.

Usage: python3 scripts/check_module_realizations.py [--verbose]
"""
import argparse
import re
import sys
from pathlib import Path

AGENT_ROOT = Path(__file__).parent.parent
MAGPIE_ROOT = AGENT_ROOT.parent
MODULES_DOC_DIR = AGENT_ROOT / "modules"
MODULES_CODE_DIR = MAGPIE_ROOT / "modules"
CONFIG_DEFAULT = MAGPIE_ROOT / "config" / "default.cfg"

# Matches lines like: cfg$gms$yields <- "managementcalib_aug19"
CONFIG_RE = re.compile(
    r'^\s*cfg\$gms\$(?P<key>[a-z_]+)\s*<-\s*"(?P<value>[^"]+)"'
)

# Matches the module header line like:
#   # Module 14: Yields (managementcalib_aug19)
#   # Module 14_yields
#   **Realization:** `managementcalib_aug19`
#   **Realization**: managementcalib_aug19
HEADER_REAL_RE = re.compile(
    r'\*\*Realization\*\*:?\s*`?(?P<real>[a-zA-Z_][\w]*)`?'
)
# Matches "Verified Against:" footer paths like:
#   ../modules/14_yields/managementcalib_aug19/*.gms
#   ../modules/17_*/sector_may15/*.gms  (glob form — name part is `*`)
VERIFIED_RE = re.compile(
    r'(?:Verified\s+Against|verified\s+against)[:\s\*]+`?\.{1,2}/modules/(?P<num>\d+)_(?P<name>[a-z_*]+)/(?P<real>[a-zA-Z][\w]*)/'
)

# Module-number → -doc-file
MODULE_DOC_RE = re.compile(r'module_(\d+)\.md$')


def load_default_realizations():
    """Parse default.cfg and return {config_key: default_realization}."""
    if not CONFIG_DEFAULT.exists():
        print(f"FATAL: {CONFIG_DEFAULT} not found", file=sys.stderr)
        sys.exit(3)
    defaults = {}
    for line in CONFIG_DEFAULT.read_text().splitlines():
        m = CONFIG_RE.match(line)
        if m:
            defaults[m.group("key")] = m.group("value")
    return defaults


def load_module_map():
    """Map module number → (dir_name, config_key).
    Config key is the dir name with the leading 'NN_' stripped."""
    mapping = {}
    if not MODULES_CODE_DIR.exists():
        print(f"FATAL: {MODULES_CODE_DIR} not found", file=sys.stderr)
        sys.exit(3)
    for child in MODULES_CODE_DIR.iterdir():
        if not child.is_dir():
            continue
        m = re.match(r'^(\d+)_(.+)$', child.name)
        if m:
            num, key = m.group(1), m.group(2)
            mapping[num] = (child.name, key)
    return mapping


def list_realization_dirs(module_dir_name):
    """Return list of realization subdirs for a module (excluding 'input', 'module.gms')."""
    mod_path = MODULES_CODE_DIR / module_dir_name
    if not mod_path.exists():
        return []
    return [
        d.name for d in mod_path.iterdir()
        if d.is_dir() and d.name not in ("input",)
    ]


def find_realization_claims(doc_text):
    """Scan a module doc and return:
       (header_realization, [(footer_realization, dir_num, dir_name), ...])"""
    header_real = None
    header_match = HEADER_REAL_RE.search(doc_text)
    if header_match:
        header_real = header_match.group("real")

    footer_claims = []
    for m in VERIFIED_RE.finditer(doc_text):
        footer_claims.append((m.group("real"), m.group("num"), m.group("name")))

    return header_real, footer_claims


def check_one_module(doc_path, defaults, module_map, verbose=False):
    """Return list of findings: (severity, message)."""
    findings = []
    m = MODULE_DOC_RE.search(doc_path.name)
    if not m:
        return findings
    num = m.group(1)

    if num not in module_map:
        findings.append(("WARN", f"{doc_path.name}: no matching module directory {num}_* exists"))
        return findings

    dir_name, config_key = module_map[num]
    expected_default = defaults.get(config_key)
    available_realizations = list_realization_dirs(dir_name)

    doc_text = doc_path.read_text()
    header_real, footer_claims = find_realization_claims(doc_text)

    # Check header-claimed realization
    if header_real is not None:
        if header_real not in available_realizations:
            findings.append((
                "ERROR",
                f"{doc_path.name}: header claims realization `{header_real}` but directory {dir_name}/ has no such subdir. Available: {available_realizations}"
            ))
        elif expected_default is not None and header_real != expected_default:
            findings.append((
                "WARN",
                f"{doc_path.name}: header claims `{header_real}` as the documented realization but config/default.cfg default is `{expected_default}`. (Documenting non-default realizations is allowed but should be clearly marked.)"
            ))

    # Check footer-cited realization
    for footer_real, footer_num, footer_name in footer_claims:
        if footer_num != num:
            findings.append((
                "WARN",
                f"{doc_path.name}: footer cites module {footer_num} but this is module {num} ({dir_name})"
            ))
        if footer_real not in available_realizations:
            findings.append((
                "ERROR",
                f"{doc_path.name}: 'Verified Against' footer cites `{footer_real}` but directory {dir_name}/ has no such subdir. Available: {available_realizations}"
            ))
        elif expected_default is not None and footer_real != expected_default:
            findings.append((
                "ERROR",
                f"{doc_path.name}: footer cites `{footer_real}` but default per config/default.cfg is `{expected_default}`. Footers should reference the default realization (the documented one)."
            ))

    if verbose and not findings:
        findings.append(("INFO", f"{doc_path.name}: OK (header=`{header_real}`, footer={[c[0] for c in footer_claims]}, default=`{expected_default}`)"))

    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--verbose", action="store_true", help="Print info lines for clean modules")
    ap.add_argument("--module", type=int, help="Check only this module number (e.g. 18)")
    args = ap.parse_args()

    defaults = load_default_realizations()
    module_map = load_module_map()

    all_findings = []
    if not MODULES_DOC_DIR.exists():
        print(f"FATAL: {MODULES_DOC_DIR} not found", file=sys.stderr)
        sys.exit(3)

    docs = sorted(MODULES_DOC_DIR.glob("module_*.md"))
    if args.module is not None:
        docs = [d for d in docs if d.name == f"module_{args.module:02d}.md"]

    for doc in docs:
        # Skip notes files (module_XX_notes.md)
        if "_notes.md" in doc.name:
            continue
        findings = check_one_module(doc, defaults, module_map, verbose=args.verbose)
        all_findings.extend(findings)

    errors = [f for f in all_findings if f[0] == "ERROR"]
    warns = [f for f in all_findings if f[0] == "WARN"]
    infos = [f for f in all_findings if f[0] == "INFO"]

    for sev, msg in all_findings:
        prefix = {"ERROR": "❌", "WARN": "⚠️ ", "INFO": "ℹ️ "}.get(sev, "  ")
        print(f"{prefix} {msg}")

    print()
    print(f"Realization-validity: {len(errors)} errors, {len(warns)} warnings, {len(docs)} module docs checked")

    if errors:
        sys.exit(1)
    if warns:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
