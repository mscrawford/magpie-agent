#!/usr/bin/env python3
"""PR impact analyzer (component 5a of S2, the PR-integration pipeline).

Given a MAgPIE commit range, produce a structured JSON report listing each
magpie-agent doc that may need updates, the change type, and a confidence tier
that downstream tooling (5b mechanical / 5c semantic) uses to dispatch.

Change classes detected:
  identifier_change   — vars/params/scalars added or removed in declarations.gms
  line_shift          — line-number citations that need offset due to diff hunks
  default_value_change — scalar default value changed in input.gms
  new_realization     — new modules/NN_x/REALIZATION/ directory

Confidence tiers (in `affected_docs` entries):
  mechanical — pure data transform; 5b can apply unattended
  semantic   — needs prose update; 5c spawns an agent + auditor
  manual     — ambiguous; flag for maintainer

Usage:
  pr_doc_impact.py --base <sha> --head <sha> [--output FILE]
  pr_doc_impact.py --since-last-sync                   # base = sync_log last_sync_commit
  pr_doc_impact.py --pr <N>                            # base/head via gh
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
MAGPIE_DIR = AGENT_DIR.parent

sys.path.insert(0, str(SCRIPT_DIR))
from check_gams_variables import (  # noqa: E402
    GAMS_INTERFACE_RE,
    GAMS_NUMBERED_RE,
)

# --- Regexes -----------------------------------------------------------------

# Any interface or numbered GAMS identifier (for token scans in docs).
ANY_VAR_RE = re.compile(
    r"\b(?:" + GAMS_INTERFACE_RE.pattern[2:] + "|" + GAMS_NUMBERED_RE.pattern[2:] + r")"
)

# Declarations.gms parameter/variable line (mirrors check_consumer_attribution.py).
DECL_LINE_RE = re.compile(
    r"^\s*(?P<name>[a-z][a-zA-Z0-9_]+)\s*(?:\([^)]+\))?\s+\S+"
)
DECL_SECTION_KEYWORDS = {
    "parameters", "parameter", "variables", "variable",
    "positive", "negative", "free", "binary", "integer",
    "equations", "equation", "scalars", "scalar", "sets", "set",
    "table", "tables", "alias",
}

# Scalar declaration line: `sNN_name [(...)] description (units) / VALUE /`.
SCALAR_DECL_RE = re.compile(
    r"^\s*(?P<name>s\d+_[a-zA-Z0-9_]+|s_[a-zA-Z0-9_]+|sm_[a-zA-Z0-9_]+)\b.*?/\s*(?P<value>[-+\d.eE]+)\s*/"
)

# Diff hunk header: @@ -A,B +C,D @@
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

# File:line citation pattern. Captures the .gms filename and the cited line.
# We resolve filename → changed-file path via the gms-filename match.
CITATION_RE = re.compile(r"`?(?P<file>[\w]+)\.gms:(?P<line>\d+)")

# Module dir extraction from a path like modules/14_yields/managementcalib_aug19/...
MODULE_PATH_RE = re.compile(r"^modules/(\d+)_(\w+)/(\w+)/")


# --- Git helpers -------------------------------------------------------------

def run_git(cmd: list[str], cwd: Path = MAGPIE_DIR, check: bool = True) -> str:
    """Run a git command in the MAgPIE repo and return stdout."""
    return subprocess.run(
        ["git", *cmd], cwd=cwd, capture_output=True, text=True, check=check
    ).stdout


def git_file_exists(rev: str, path: str) -> bool:
    try:
        run_git(["cat-file", "-e", f"{rev}:{path}"])
        return True
    except subprocess.CalledProcessError:
        return False


def git_show(rev: str, path: str) -> str:
    try:
        return run_git(["show", f"{rev}:{path}"])
    except subprocess.CalledProcessError:
        return ""


def changed_files(base: str, head: str) -> list[tuple[str, str]]:
    """Return (status, path) for each changed file. Status: A/M/D/R..."""
    out = run_git(["diff", "--name-status", f"{base}..{head}"])
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0][:1]
        # Renamed: status starts with R; final path is the new name (parts[-1]).
        path = parts[-1]
        rows.append((status, path))
    return rows


# --- Change detectors --------------------------------------------------------

def detect_identifier_changes(base: str, head: str, decl_path: str) -> dict[str, list[str]]:
    """Diff a declarations.gms; return net added/removed identifier names.

    Uses -U0 so the diff lines map cleanly to declaration lines.
    """
    diff = run_git(["diff", "-U0", f"{base}..{head}", "--", decl_path])
    added: set[str] = set()
    removed: set[str] = set()
    for line in diff.splitlines():
        if line.startswith(("+++", "---", "@@")):
            continue
        if not line:
            continue
        sign = line[0]
        content = line[1:]
        m = DECL_LINE_RE.match(content)
        if not m:
            continue
        name = m.group("name").lower()
        if name in DECL_SECTION_KEYWORDS:
            continue
        # Require ANY_VAR_RE-shape to avoid catching prose / set names declared elsewhere.
        if not ANY_VAR_RE.match(m.group("name")):
            continue
        if sign == "+":
            added.add(m.group("name"))
        elif sign == "-":
            removed.add(m.group("name"))
    return {
        "added": sorted(added - removed),
        "removed": sorted(removed - added),
    }


def detect_scalar_value_changes(base: str, head: str, input_path: str) -> list[dict]:
    """Parse input.gms at both revs and report scalars whose / VALUE / changed."""
    def parse(text: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for line in text.splitlines():
            m = SCALAR_DECL_RE.match(line)
            if m:
                out[m.group("name")] = m.group("value")
        return out

    old = parse(git_show(base, input_path))
    new = parse(git_show(head, input_path))
    changes = []
    for name in sorted(set(old) | set(new)):
        ov, nv = old.get(name), new.get(name)
        if ov == nv:
            continue
        kind = "added" if ov is None else "removed" if nv is None else "changed"
        changes.append({"name": name, "old_value": ov, "new_value": nv, "kind": kind})
    return changes


def detect_line_shifts(base: str, head: str, path: str) -> list[dict]:
    """Return per-hunk shift records: anchor line in OLD file + size delta."""
    diff = run_git(["diff", "-U0", f"{base}..{head}", "--", path])
    shifts = []
    for line in diff.splitlines():
        m = HUNK_RE.match(line)
        if not m:
            continue
        old_start = int(m.group(1))
        old_count = int(m.group(2)) if m.group(2) else 1
        new_count = int(m.group(4)) if m.group(4) else 1
        delta = new_count - old_count
        if delta != 0:
            # Anchor: the last unchanged line BEFORE the hunk.
            # For a pure addition at line N, old_start = N-1 with old_count=0.
            # For other hunks, use old_start as the "from" line; citations at or
            # after this line shift by delta.
            anchor = old_start if old_count > 0 else old_start
            shifts.append({"from_line": anchor, "delta": delta})
    return shifts


def detect_new_realizations(base: str, head: str) -> list[dict]:
    """Find newly added modules/NN_name/REALIZATION/ directories.

    Heuristic: any new realization.gms file under a path that did NOT
    exist at base.
    """
    added = run_git(["diff", "--diff-filter=A", "--name-only", f"{base}..{head}"]).splitlines()
    seen: set[str] = set()
    out = []
    for f in added:
        m = MODULE_PATH_RE.match(f)
        if not m:
            continue
        parts = f.split("/")
        # parts[0]=modules, parts[1]=NN_name, parts[2]=REALIZATION, parts[3]=file…
        realization_dir = "/".join(parts[:3])
        if realization_dir in seen:
            continue
        if not git_file_exists(head, f"{realization_dir}/realization.gms"):
            continue
        if git_file_exists(base, f"{realization_dir}/realization.gms"):
            continue
        seen.add(realization_dir)
        out.append({
            "module_dir": "/".join(parts[:2]),
            "realization": parts[2],
            "path": realization_dir,
        })
    return out


# --- Doc scanners ------------------------------------------------------------

def _agent_doc_paths() -> list[Path]:
    """All magpie-agent markdown docs we care about (excluding archives)."""
    out = []
    for p in AGENT_DIR.rglob("*.md"):
        if "archive" in p.parts:
            continue
        if ".git" in p.parts:
            continue
        out.append(p)
    return sorted(out)


def docs_mentioning_token(token: str) -> list[dict]:
    """Return per-doc line numbers where `token` appears as a word boundary."""
    pattern = re.compile(r"\b" + re.escape(token) + r"\b")
    hits = []
    for doc in _agent_doc_paths():
        text = doc.read_text(encoding="utf-8", errors="ignore")
        lines = [i + 1 for i, line in enumerate(text.splitlines()) if pattern.search(line)]
        if lines:
            hits.append({"doc": str(doc.relative_to(AGENT_DIR)), "lines": lines})
    return hits


def docs_citing_gms_file(changed_path: str) -> list[dict]:
    """Find citations in docs that resolve to `changed_path`.

    Match rules (avoid bare-basename false positives across modules):
      - Full path citation `modules/NN_name/REAL/file.gms:NN` → match if path equals
        the changed file.
      - Bare basename `file.gms:NN` → match ONLY in `modules/module_NN.md` or its
        `_notes.md` companion, where the module number derives from `changed_path`.
    """
    m = MODULE_PATH_RE.match(changed_path)
    if not m:
        return []
    module_num = m.group(1)
    gms_filename = Path(changed_path).stem  # e.g. "equations"
    module_doc_names = {
        f"modules/module_{module_num}.md",
        f"modules/module_{module_num}_notes.md",
    }

    full_path_re = re.compile(
        r"`?" + re.escape(changed_path) + r":(?P<line>\d+)"
    )

    hits = []
    for doc in _agent_doc_paths():
        rel = str(doc.relative_to(AGENT_DIR))
        text = doc.read_text(encoding="utf-8", errors="ignore")
        citations = []
        is_module_doc = rel in module_doc_names
        for i, line in enumerate(text.splitlines(), 1):
            # Always match full-path citations
            for fm in full_path_re.finditer(line):
                citations.append({"doc_line": i, "cited_line": int(fm.group("line"))})
            # Bare basenames only in the matching module doc
            if is_module_doc:
                for cm in CITATION_RE.finditer(line):
                    if cm.group("file") == gms_filename:
                        # Skip if this same span was already captured as a full-path cite
                        # (the full-path regex contains the bare one as a substring).
                        if any(cit["doc_line"] == i and cit["cited_line"] == int(cm.group("line"))
                               for cit in citations):
                            continue
                        citations.append({"doc_line": i, "cited_line": int(cm.group("line"))})
        if citations:
            hits.append({"doc": rel, "citations": citations})
    return hits


def doc_for_module(module_dir: str) -> str | None:
    """modules/14_yields → modules/module_14.md if it exists."""
    m = re.match(r"^modules/(\d+)_", module_dir)
    if not m:
        return None
    candidate = AGENT_DIR / "modules" / f"module_{m.group(1)}.md"
    return f"modules/module_{m.group(1)}.md" if candidate.is_file() else None


# --- Report assembly ---------------------------------------------------------

def assemble_report(base: str, head: str) -> dict:
    """Top-level: walk changed files; emit `changes` array with affected_docs nested."""
    files = changed_files(base, head)

    changes: list[dict] = []

    # 1. Identifier changes (per declarations.gms) — deduplicate by name across
    # multi-realization modules so vm_X added in 3 realizations is one finding.
    added_by_name: dict[str, list[str]] = defaultdict(list)
    removed_by_name: dict[str, list[str]] = defaultdict(list)
    for status, path in files:
        if not path.endswith("declarations.gms") or status == "D":
            continue
        idents = detect_identifier_changes(base, head, path)
        for name in idents["added"]:
            added_by_name[name].append(path)
        for name in idents["removed"]:
            removed_by_name[name].append(path)

    for name, paths in sorted(added_by_name.items()):
        module_doc = doc_for_module(paths[0])
        affected = []
        if module_doc:
            affected.append({"doc": module_doc, "confidence": "semantic",
                             "reason": "new identifier — add description"})
        changes.append({
            "type": "identifier_added",
            "name": name,
            "in_files": paths,
            "affected_docs": affected,
        })

    for name, paths in sorted(removed_by_name.items()):
        doc_hits = docs_mentioning_token(name)
        affected = [{"doc": h["doc"], "lines": h["lines"], "confidence": "semantic",
                     "reason": "identifier removed — stale references"} for h in doc_hits]
        # Skip removals with no stale references — nothing to update.
        if not affected:
            continue
        changes.append({
            "type": "identifier_removed",
            "name": name,
            "in_files": paths,
            "affected_docs": affected,
        })

    # 2. Default-value changes (per input.gms)
    for status, path in files:
        if not path.endswith("input.gms") or status == "D":
            continue
        for change in detect_scalar_value_changes(base, head, path):
            doc_hits = docs_mentioning_token(change["name"])
            affected = [{"doc": h["doc"], "lines": h["lines"], "confidence": "manual",
                         "reason": "scalar default value changed — verify cited number"} for h in doc_hits]
            changes.append({
                "type": "default_value_change",
                "name": change["name"],
                "old_value": change["old_value"],
                "new_value": change["new_value"],
                "kind": change["kind"],
                "in_file": path,
                "affected_docs": affected,
            })

    # 3. Line shifts (any .gms file with hunks)
    for status, path in files:
        if not path.endswith(".gms") or status in ("A", "D"):
            continue
        shifts = detect_line_shifts(base, head, path)
        if not shifts:
            continue
        cite_hits = docs_citing_gms_file(path)
        if not cite_hits:
            continue
        affected = []
        for h in cite_hits:
            # Apply shifts: for each citation, sum deltas of all hunks with from_line <= cited_line
            shifted = []
            for c in h["citations"]:
                cumulative = sum(s["delta"] for s in shifts if s["from_line"] <= c["cited_line"])
                if cumulative != 0:
                    shifted.append({
                        "doc_line": c["doc_line"],
                        "cited_line": c["cited_line"],
                        "suggested_line": c["cited_line"] + cumulative,
                    })
            if shifted:
                affected.append({"doc": h["doc"], "shifts": shifted,
                                 "confidence": "mechanical",
                                 "reason": "cited line numbers shifted"})
        if affected:
            changes.append({
                "type": "line_shift",
                "in_file": path,
                "hunks": shifts,
                "affected_docs": affected,
            })

    # 4. New realizations
    for nr in detect_new_realizations(base, head):
        module_doc = doc_for_module(nr["module_dir"])
        affected = []
        if module_doc:
            affected.append({"doc": module_doc, "confidence": "semantic",
                             "reason": "new realization — add to realization comparison section"})
        affected.append({"doc": "AGENT.md", "confidence": "manual",
                         "reason": "may need entry in 'Modules with multiple realizations' list"})
        changes.append({
            "type": "new_realization",
            "module_dir": nr["module_dir"],
            "realization": nr["realization"],
            "path": nr["path"],
            "affected_docs": affected,
        })

    # Pivot: build per-doc index for downstream consumers.
    by_doc: dict[str, list[dict]] = defaultdict(list)
    for change in changes:
        for affected in change.get("affected_docs", []):
            by_doc[affected["doc"]].append({
                "change_type": change["type"],
                "confidence": affected["confidence"],
                "reason": affected["reason"],
                "details": {k: v for k, v in change.items() if k != "affected_docs"},
            })

    return {
        "base": base,
        "head": head,
        "changes": changes,
        "docs_affected": [
            {"doc": doc, "entries": entries}
            for doc, entries in sorted(by_doc.items())
        ],
        "summary": {
            "total_changes": len(changes),
            "by_type": dict(_count_by(changes, "type")),
            "docs_touched": len(by_doc),
        },
    }


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for it in items:
        out[it[key]] += 1
    return out


# --- Entry point -------------------------------------------------------------

def resolve_base_head(args) -> tuple[str, str]:
    if args.since_last_sync:
        log = json.loads((AGENT_DIR / "project" / "sync_log.json").read_text())
        return log["sync_status"]["last_sync_commit"], args.head or "develop"
    if args.pr:
        info = subprocess.run(
            ["gh", "pr", "view", str(args.pr), "--json", "baseRefOid,headRefOid"],
            cwd=MAGPIE_DIR, capture_output=True, text=True, check=True,
        )
        data = json.loads(info.stdout)
        return data["baseRefOid"], data["headRefOid"]
    if not args.base or not args.head:
        raise SystemExit("--base and --head required (or --since-last-sync or --pr)")
    return args.base, args.head


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", help="Base commit SHA")
    ap.add_argument("--head", help="Head commit SHA (default: develop with --since-last-sync)")
    ap.add_argument("--since-last-sync", action="store_true",
                    help="Use sync_log.json's last_sync_commit as base")
    ap.add_argument("--pr", type=int, help="GitHub PR number (uses gh)")
    ap.add_argument("--output", help="Output JSON file (default: stdout)")
    ap.add_argument("--pretty", action="store_true", help="Indented JSON output")
    args = ap.parse_args()

    base, head = resolve_base_head(args)
    report = assemble_report(base, head)
    payload = json.dumps(report, indent=2 if args.pretty else None)
    if args.output:
        Path(args.output).write_text(payload + "\n")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
