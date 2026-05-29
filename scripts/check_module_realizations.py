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
4. NEW (R3 Phase B, 2026-05-23): walk body file:line citations and flag when
   the DOMINANT cited realization differs from the header — this catches
   M38/M30 class where the doc header correctly names the default but the
   body content cites a non-default realization. Threshold: dominant > 50%
   of self-module body cites.

Closes R1 audit Cluster 1 (Module 18 wrong-realization CRITICAL + 13/46
footer fabrications) and R3 Cluster 1 (multi-realization body drift).

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
#   **Realization:** `managementcalib_aug19`     (colon INSIDE bold)
#   **Realization**: managementcalib_aug19       (colon OUTSIDE bold)
#   Realization: managementcalib_aug19           (no bold)
# R3 fix (2026-05-23): accept all four colon-placement variants;
# previously only matched "**Realization**:" exactly.
HEADER_REAL_RE = re.compile(
    r'\*{0,2}Realization\*{0,2}\s*:\s*\*{0,2}\s*`?(?P<real>[a-zA-Z_][\w]*)`?'
)
# "Verified Against" footer parsing is now two-stage:
# 1) VERIFIED_LINE_RE identifies the footer line and captures the rest of the line.
# 2) PATH_RE finds ALL `modules/NN_name/realization/` paths within that line.
# I3 fix (2026-05-24): previously this was a single regex anchored on
# "Verified Against" + first path, which silently dropped any additional paths
# in multi-path footers (e.g. M18's flexreg_apr16 default body + flexcluster_jul23
# alternative summary). Now all cited realizations are validated.
VERIFIED_LINE_RE = re.compile(
    # Footer-ANCHORED (R27 fix): the match must be a line-start label of the form
    # "[bullet] **Verified Against**: ..." (colon required). Previously this matched
    # "verified against" ANYWHERE via finditer over the whole doc, so inline prose
    # ("(verified against GAMS code)", "formulas verified against equations.gms",
    # and an R27 inline "(verified against modules/11_costs/default/...)" ) was
    # misread as a footer realization claim — the latter wrongly flagged module_40
    # as citing realization `default`. Corpus survey: 50 real footers are all
    # line-start "**Verified Against**:"; 50 inline occurrences are all mid-line.
    # The line-start + colon-label discriminator keeps the 50 footers and drops the
    # 50 inline cases. Verify with --self-test.
    r'(?im)^\s*(?:[-*]\s*)?\*{0,2}\s*Verified\s+Against\s*\*{0,2}\s*:\s*(?P<rest>[^\n]+)'
)
PATH_RE = re.compile(
    r'`?(?:\.{1,2}/)?modules/(?P<num>\d+)_(?P<name>[a-z_*]+)/(?P<real>[a-zA-Z][\w]*)/'
)
# Backwards-compat alias for any external imports.
VERIFIED_RE = VERIFIED_LINE_RE

# Module-number → -doc-file
MODULE_DOC_RE = re.compile(r'module_(\d+)\.md$')

# Body citation regex: matches `modules/NN_name/<realization>/<file>.gms[:LL]`
# Used by the body-realization-mismatch check (R3 Phase B).
BODY_CITE_RE = re.compile(
    r'modules/(?P<num>\d+)_(?P<name>[a-z_]+)/(?P<real>[a-zA-Z][\w]*)/[\w./]+\.gms'
)


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
    seen = set()
    for line_match in VERIFIED_LINE_RE.finditer(doc_text):
        rest = line_match.group("rest")
        for m in PATH_RE.finditer(rest):
            claim = (m.group("real"), m.group("num"), m.group("name"))
            if claim in seen:
                continue
            seen.add(claim)
            footer_claims.append(claim)

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

    # Check footer-cited realization.
    # I3 (2026-05-24): with multi-path footer parsing, footers may explicitly
    # cite the default PLUS one or more documented alternatives (e.g. M18, M38,
    # M80). A non-default claim is only an ERROR when no other claim in the
    # same doc cites the default — otherwise it's a documented alternative
    # (INFO-only, doesn't surface in normal output).
    any_footer_matches_default = expected_default is not None and any(
        fr == expected_default for fr, _, _ in footer_claims
    )
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
            if any_footer_matches_default:
                if verbose:
                    findings.append((
                        "INFO",
                        f"{doc_path.name}: footer also cites alternative realization `{footer_real}` (default `{expected_default}` is cited elsewhere in the footer)"
                    ))
            else:
                findings.append((
                    "ERROR",
                    f"{doc_path.name}: footer cites `{footer_real}` but default per config/default.cfg is `{expected_default}`. Footers should reference the default realization (the documented one)."
                ))

    # R3 Phase B: body-realization-mismatch — count self-module body cites,
    # flag when the dominant realization differs from the header. This catches
    # M38/M30/M80 class where the header is correct but the body describes
    # a non-default realization (citation paths reveal it).
    #
    # Suppression: if the header-claimed realization has zero q<NN>_ equations
    # (e.g., M37 default `off`, M80 default `nlp_apr17` solver-orchestration),
    # the body MUST describe an alternative — that's a structural requirement,
    # not a bug.
    if header_real is not None:
        # Check whether the header-claimed realization has any equations
        default_eqns = MODULES_CODE_DIR / dir_name / header_real / "equations.gms"
        header_has_equations = False
        if default_eqns.is_file():
            for line in default_eqns.read_text().splitlines():
                if re.match(rf'^\s*q{num}_', line):
                    header_has_equations = True
                    break

        if header_has_equations:
            body_real_counts = {}
            for cm in BODY_CITE_RE.finditer(doc_text):
                if cm.group("num") != num:
                    continue  # cross-module citation, not this module's body
                body_real_counts[cm.group("real")] = body_real_counts.get(cm.group("real"), 0) + 1
            total_body_cites = sum(body_real_counts.values())
            if total_body_cites >= 3:  # need a few cites before we can talk about dominance
                dominant_real = max(body_real_counts, key=body_real_counts.get)
                dominant_count = body_real_counts[dominant_real]
                if dominant_real != header_real and dominant_count * 2 > total_body_cites:
                    # Dominant realization in body != header claim, AND it's >50% of cites
                    others = {r: c for r, c in body_real_counts.items() if r != dominant_real}
                    findings.append((
                        "WARN",
                        f"{doc_path.name}: header claims `{header_real}` but body cites `{dominant_real}` in {dominant_count}/{total_body_cites} self-module file:line references (other: {others}). Body content may describe a non-default realization."
                    ))

    if verbose and not findings:
        findings.append(("INFO", f"{doc_path.name}: OK (header=`{header_real}`, footer={[c[0] for c in footer_claims]}, default=`{expected_default}`)"))

    return findings


def _self_test():
    """Positive control: inline 'verified against' prose must NOT parse as a footer
    claim; real line-start footers MUST. Returns exit code."""
    failures = []
    inline = (
        "# Module 40\n"
        "**Source**: `declarations.gms` (verified against GAMS code)\n"
        "All formulas verified against `equations.gms`.\n"
        "Usage in Module 11 (verified against `modules/11_costs/default/equations.gms`).\n"
    )
    _h, claims = find_realization_claims(inline)
    if claims:
        failures.append(f"inline prose parsed as footer claims: {claims}")
    footer = (
        "# Module 40\n\n"
        "**Verified Against**: `../modules/40_transport/gtap_nov12/equations.gms`\n"
    )
    _h, claims = find_realization_claims(footer)
    if claims != [("gtap_nov12", "40", "transport")]:
        failures.append(f"real footer not parsed: {claims}")
    footer2 = "**Verified Against:** `modules/11_costs/default/equations.gms`\n"
    _h, claims = find_realization_claims(footer2)
    if claims != [("default", "11", "costs")]:
        failures.append(f"colon-inside-bold footer not parsed: {claims}")
    if failures:
        print("SELF-TEST FAILED:", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        return 1
    print("SELF-TEST OK - inline 'verified against' prose ignored; line-start "
          "footers parsed.", file=sys.stderr)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--verbose", action="store_true", help="Print info lines for clean modules")
    ap.add_argument("--module", type=int, help="Check only this module number (e.g. 18)")
    ap.add_argument("--self-test", action="store_true",
                    help="Run in-memory positive-control tests and exit.")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(_self_test())

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
