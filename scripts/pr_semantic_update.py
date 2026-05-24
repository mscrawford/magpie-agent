#!/usr/bin/env python3
"""Semantic updater (component 5c of S2, the PR-integration pipeline).

Reads a 5a impact-report JSON and processes `confidence: semantic` entries via
a writer/auditor LLM pipeline:
  1. Writer (sonnet) drafts a focused doc edit given the GAMS change and
     current doc state.
  2. Auditor (sonnet for MVP; can swap to opus) scores the edit 1-10 against
     actual GAMS source. >=8: pass. <8: escalate.

Auto-applies passing edits to the working tree (never commits). Below-threshold
edits write escalation files to /tmp/magpie_5c_escalations/ for human review.

MVP scope: identifier_added only. identifier_removed and new_realization
deferred (require more complex edit semantics).

Requires:
  pip install claude-agent-sdk
  Authentication via Claude Code CLI (same auth as `claude` command).

Usage:
  pr_semantic_update.py --input REPORT.json [--apply] [--limit N] [--verbose]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        query,
    )
except ImportError:
    print("ERROR: claude_agent_sdk not installed. Run: pip install claude-agent-sdk",
          file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_DIR = SCRIPT_DIR.parent
MAGPIE_DIR = AGENT_DIR.parent
ESCALATION_DIR = Path("/tmp/magpie_5c_escalations")

WRITER_MODEL = "claude-sonnet-4-6"
AUDITOR_MODEL = "claude-sonnet-4-6"  # MVP; opus recommended for production

WRITER_SYSTEM = (
    "You are a MAgPIE documentation editor. Given a new GAMS identifier and "
    "the current state of a module doc, propose a focused, accurate description. "
    "Output ONLY valid JSON — no preamble, no markdown fences."
)

AUDITOR_SYSTEM = (
    "You audit proposed MAgPIE doc edits against actual GAMS source. "
    "Score 1-10; cite specific bugs (wrong names, wrong dimensions, fabricated "
    "identifiers, missing citations). Output ONLY valid JSON — no preamble."
)


# --- Helpers -----------------------------------------------------------------

def find_declaration_context(file_path: str, name: str, window: int = 10) -> str:
    """Return ±window lines around the line that declares `name`."""
    p = MAGPIE_DIR / file_path
    if not p.is_file():
        return ""
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, line in enumerate(lines):
        if re.search(r"\b" + re.escape(name) + r"\b", line):
            start = max(0, i - window)
            end = min(len(lines), i + window + 1)
            return "\n".join(lines[start:end])
    return ""


def parse_json_loose(text: str) -> dict | None:
    """Parse JSON from LLM output, tolerating fences and stray prose."""
    text = text.strip()
    # Strip markdown fences if present
    fence = re.match(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first balanced {...}
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


async def call_llm(system: str, user_prompt: str, model: str) -> tuple[str, float]:
    """Single LLM call with tools disabled. Returns (text, cost_usd)."""
    options = ClaudeAgentOptions(
        system_prompt=system,
        max_turns=3,
        allowed_tools=[],
        model=model,
    )
    text = ""
    cost = 0.0
    async for msg in query(prompt=user_prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for b in msg.content:
                if hasattr(b, "text"):
                    text += b.text
        elif isinstance(msg, ResultMessage):
            cost = msg.total_cost_usd or 0.0
    return text, cost


# --- Writer & auditor for identifier_added -----------------------------------

async def write_identifier_addition(change: dict, doc_path: Path) -> tuple[dict | None, float]:
    name = change["name"]
    in_file = change["in_files"][0]
    decl_ctx = find_declaration_context(in_file, name)
    doc_text = doc_path.read_text(encoding="utf-8", errors="ignore")
    doc_excerpt = doc_text[:8000]

    prompt = f"""Add a description of new GAMS identifier `{name}` to the module doc.

== Identifier ==
Name: `{name}`
Declared in: `{in_file}`

== GAMS declaration excerpt (with context) ==
```gams
{decl_ctx}
```

== Current doc (first ~8000 chars) ==
File: {doc_path.relative_to(AGENT_DIR)}
```markdown
{doc_excerpt}
```

== Output ==
Return JSON ONLY (no markdown fences):
{{
  "section_to_modify": "<exact section header from the doc where addition belongs>",
  "insert_after_line": <integer line number in the doc>,
  "new_content": "<markdown text to insert (1-5 lines, use full-path citations modules/NN_name/REAL/file.gms:N)>",
  "rationale": "<one-sentence reasoning>"
}}

If the doc already mentions this identifier, return:
{{"section_to_modify": null, "insert_after_line": null, "new_content": null, "rationale": "already documented"}}
"""
    text, cost = await call_llm(WRITER_SYSTEM, prompt, WRITER_MODEL)
    return parse_json_loose(text), cost


async def audit_identifier_edit(
    change: dict, edit: dict, doc_path: Path
) -> tuple[dict | None, float]:
    name = change["name"]
    in_file = change["in_files"][0]
    decl_ctx = find_declaration_context(in_file, name, window=15)

    prompt = f"""Audit this proposed MAgPIE doc edit for accuracy against actual GAMS source.

== Proposed addition to `{doc_path.relative_to(AGENT_DIR)}` ==
After line {edit.get('insert_after_line')} in section "{edit.get('section_to_modify')}":
```markdown
{edit.get('new_content')}
```

== Actual GAMS declaration ==
File: `{in_file}`
```gams
{decl_ctx}
```

== Audit criteria ==
- Identifier name spelled exactly as in GAMS source?
- Dimensions match the declaration (e.g., `(t,i,type)`)?
- Units stated correctly (from declaration comment)?
- All file:line citations use full-path form `modules/NN_name/REAL/file.gms:N`?
- No fabricated identifiers in the surrounding prose?
- Description faithfully reflects the declaration (no embellishment, no inferred behavior beyond what the code says)?

Score 1-10. >=8 means ship. Below 8: list specific bugs.

Return JSON ONLY:
{{
  "score": <integer 1-10>,
  "issues": ["<specific bug 1>", "<specific bug 2>"]
}}
"""
    text, cost = await call_llm(AUDITOR_SYSTEM, prompt, AUDITOR_MODEL)
    return parse_json_loose(text), cost


# --- Edit application and escalation ----------------------------------------

def apply_edit(doc_path: Path, edit: dict) -> bool:
    if not edit.get("new_content") or edit.get("insert_after_line") is None:
        return False
    text = doc_path.read_text(encoding="utf-8", errors="ignore")
    has_nl = text.endswith("\n")
    lines = text.splitlines()
    after = int(edit["insert_after_line"])
    if after < 0 or after > len(lines):
        return False
    new_lines = lines[:after] + edit["new_content"].splitlines() + lines[after:]
    out = "\n".join(new_lines)
    if has_nl:
        out += "\n"
    doc_path.write_text(out, encoding="utf-8")
    return True


def escalate(change: dict, edit: dict | None, audit: dict | None, reason: str) -> Path:
    ESCALATION_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.-]", "_", change.get("name", "unknown"))
    p = ESCALATION_DIR / f"{change['type']}_{safe}.md"
    p.write_text(
        f"# Escalation: {change['type']} for `{change.get('name')}`\n\n"
        f"**Reason**: {reason}\n\n"
        f"## Change\n```json\n{json.dumps(change, indent=2)}\n```\n\n"
        f"## Writer output\n```json\n{json.dumps(edit, indent=2) if edit else '(none)'}\n```\n\n"
        f"## Auditor output\n```json\n{json.dumps(audit, indent=2) if audit else '(none)'}\n```\n"
    )
    return p


async def process_identifier_added(
    change: dict, apply_changes: bool, verbose: bool
) -> dict | None:
    semantic_docs = [
        ad for ad in change.get("affected_docs", [])
        if ad.get("confidence") == "semantic"
    ]
    if not semantic_docs:
        return None
    doc_rel = semantic_docs[0]["doc"]
    doc_path = AGENT_DIR / doc_rel
    if not doc_path.is_file():
        return {"status": "skipped_no_doc", "name": change["name"], "doc": doc_rel}

    name = change["name"]
    total_cost = 0.0

    if verbose:
        print(f"  WRITER {name} -> {doc_rel}")
    edit, c1 = await write_identifier_addition(change, doc_path)
    total_cost += c1
    if not edit:
        return {"status": "writer_failed", "name": name, "doc": doc_rel, "cost": total_cost}
    if edit.get("rationale") == "already documented":
        return {"status": "already_documented", "name": name, "doc": doc_rel, "cost": total_cost}

    if verbose:
        print(f"  AUDITOR {name}")
    audit, c2 = await audit_identifier_edit(change, edit, doc_path)
    total_cost += c2
    if not audit:
        escalate(change, edit, None, "auditor returned unparseable output")
        return {"status": "auditor_failed", "name": name, "doc": doc_rel, "cost": total_cost}

    score = audit.get("score", 0)
    if score >= 8:
        if apply_changes:
            if apply_edit(doc_path, edit):
                return {"status": "applied", "name": name, "doc": doc_rel,
                        "score": score, "cost": total_cost}
            return {"status": "apply_failed", "name": name, "doc": doc_rel,
                    "score": score, "cost": total_cost}
        return {"status": "passed_audit_dry_run", "name": name, "doc": doc_rel,
                "score": score, "cost": total_cost}

    p = escalate(change, edit, audit, f"auditor score {score} < 8")
    return {"status": "escalated", "name": name, "doc": doc_rel,
            "score": score, "escalation": str(p), "cost": total_cost}


# --- Driver ------------------------------------------------------------------

async def main_async(args) -> int:
    report = json.loads(Path(args.input).read_text())
    targets = [
        c for c in report.get("changes", [])
        if c.get("type") == "identifier_added"
        and any(ad.get("confidence") == "semantic" for ad in c.get("affected_docs", []))
    ]
    if not targets:
        print("No identifier_added changes with semantic confidence to process.")
        return 0

    if args.limit:
        targets = targets[: args.limit]

    print(f"Processing {len(targets)} identifier_added changes...")
    if not args.apply:
        print("(dry-run; no doc writes)")

    results: list[dict] = []
    total_cost = 0.0
    for i, change in enumerate(targets):
        if args.verbose:
            print(f"\n[{i + 1}/{len(targets)}] {change['name']}")
        try:
            result = await process_identifier_added(change, args.apply, args.verbose)
        except Exception as e:
            result = {"status": "error", "name": change["name"], "error": str(e)}
        if result:
            results.append(result)
            total_cost += result.get("cost", 0.0)

    print("\n=== Summary ===")
    print(f"Total processed: {len(results)}")
    for status, n in sorted(Counter(r["status"] for r in results).items()):
        print(f"  {status}: {n}")
    print(f"Total cost: ${total_cost:.4f}")
    if any(r["status"] == "escalated" for r in results):
        print(f"\nEscalation files in {ESCALATION_DIR}/")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, help="5a JSON report")
    ap.add_argument("--apply", action="store_true",
                    help="Write changes to working tree (default: dry-run)")
    ap.add_argument("--limit", type=int, help="Limit to N changes (for testing)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
