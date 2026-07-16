#!/usr/bin/env python3
"""check_attribution_omissions.py — role-resolved OMISSION + phantom checker.

The completeness complement to the two 2026-07-15 phantom checkers
(`check_attribution_tables.py`, `check_attribution_prose.py`). Those flag a
module claimed as related to a var it references NOWHERE (a PHANTOM). They
deliberately do NOT flag OMISSIONS — a *real* consumer/producer that a doc's
list leaves out — because `build_consumer_map` over-lists (declarer + comment
mentions), so a naive "in the code-set but not the doc-list" test is noisy.
That omission direction is exactly what hid **Module 58** from module_32's
cross-module graph in R54 (the highest-severity, longest-surviving bug class).

WHAT'S NEW: a ROLE-RESOLVED reference map computed from code
--------------------------------------------------------------------------
`build_role_map()` walks every *.gms under `<MAGPIE_DIR>/modules/`, strips
comments, and classifies each occurrence of a cross-module interface var
(vm_/pm_/im_/pcm_/fm_) as POPULATE or READ:

  * POPULATE  — the var is the LEADING identifier of an equation LHS
                (`qNN.. VAR(dims) =e= ...`) or of an assignment LHS
                (`VAR(dims) = ...`, `VAR.fx/.lo/.up/.l(dims) = ...`).
                Leading-identifier-only, so a var inside a `sum()` on the LHS,
                or inside a `$()` condition, is NOT a false populate. Ambiguity
                (multi-line, macro, no clear LHS) defaults to READ — a false
                populate-omission is therefore structurally impossible.
  * READ      — anywhere else in a statement (RHS, `.l/.m` attribute reads,
                domain/condition, macro args).
  * excluded  — comment-only mentions never enter the role map (comments are
                stripped first). THIS is what makes the omission direction
                reliable where the referenced-anywhere map was too noisy.

DECLARE comes from `build_producer_map` (declarations.gms). REF_ANY (the
referenced-anywhere superset, incl. comments + declarer) is `build_consumer_map`
and is kept ONLY as the phantom denominator (conservative: if a module mentions
a var even in a comment, we do not call it a phantom).

DOC SIDE (precision over recall — honest coverage denominator on every run)
--------------------------------------------------------------------------
Parses the two highest-value MULTI-module attribution forms the single-module
prose checker throws away:
  (A) var-anchored list: a line naming EXACTLY ONE backticked cross-iface var
      with a consumer/producer trigger, e.g. (module_10.md:315-316)
        **Direct consumers of `vm_land`** (10 modules ...):
        - 22_land_conservation, 29_cropland, 30_croparea, ...
      binds the module list on that line AND the immediately-following bullet
      list to the var + direction (READ vs POPULATE).
  (B) inline single-var multi-module, e.g. (module_52.md:290)
        **Writes** `pm_..._ac` (... consumed by Module 14 `...` and Module 35 `...`)

Then, role-matched:
  * OMISSION  — a module in the code-derived role set (matching the stated
                direction) absent from the doc's list, minus the declarer and
                the doc's own module. Realization-scope aware: an omission whose
                only code references live in a NON-default realization is tagged
                low-confidence, not dropped.
  * PHANTOM   — a listed module absent from REF_ANY (references the var nowhere).

FP guards (each defends a live corpus class, mirrored from check_attribution_prose):
  negation ("does NOT consume"), historical/changelog wording, fenced code,
  de-backticking before module extraction (a `73_timber/default` path is not
  "Module 73"), partial-list hedges ("primary/key/e.g./etc" suppress OMISSIONS
  but not phantoms), declarer/doc-own-module exclusion.

Omissions are INHERENTLY lower-confidence than phantoms (a doc may legitimately
list only key consumers). They are ADVISORY and must pass adversarial refutation
+ human confirmation before any doc edit.

Ground truth: `<MAGPIE_DIR>/modules`. Point MAGPIE_DIR at a pinned develop
worktree for an authoritative run (the working tree can lag; see memory
magpie_agent_sync_against_develop):
    MAGPIE_DIR=/path/to/develop-worktree python3 check_attribution_omissions.py

Usage:
  python3 check_attribution_omissions.py [--summary-only] [--verbose]
  python3 check_attribution_omissions.py --dump-rolemap [--out FILE]   # JSON for the LLM layer
  python3 check_attribution_omissions.py --self-test                    # hermetic positive control

Exit: 0 always in scan mode (advisory). --self-test returns 0/1.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_gams_variables import (  # noqa: E402
    GAMS_INTERFACE_RE,
    MAGPIE_DIR,
    read_text_or_empty,
)
from check_consumer_attribution import (  # noqa: E402
    build_consumer_map,
    build_producer_map,
    is_interface_var,
    strip_dims,
)
from check_attribution_prose import (  # noqa: E402
    BACKTICK_TOKEN_RE,
    HISTORICAL_RE,
    MODNAME_RE,
    MODULE_WORD_RE,
    NEGATION_RE,
)

AGENT_DIR = SCRIPT_DIR.parent
DOCS_DIR = AGENT_DIR / "modules"
CROSS_DIR = AGENT_DIR / "cross_module"
CHECK_NAME = "check_attribution_omissions"

# Cross-module interface prefixes (MANDATE-18 core set + fm_ input params).
CROSS_IFACE_RE = re.compile(r"^(?:vm|pm|im|pcm|fm)_[a-z]")

# ---------------------------------------------------------------------------
# CODE SIDE — the role-resolved reference map
# ---------------------------------------------------------------------------

# GAMS relational operators (equation bodies). Case-insensitive for safety.
REL_OP_RE = re.compile(r"=[elgnELGN]=")
# Operators to MASK before locating a bare assignment '=' (same-length replace so
# offsets into the original statement stay valid).
_MASK_OPS_RE = re.compile(r"=[elgnELGN]=|==|>=|<=|=>|=<|<>")
# Leading identifier of an LHS (skip a leading sign / open paren).
_LEAD_ID_RE = re.compile(r"\s*[-+(]*\s*([A-Za-z][A-Za-z0-9_]*)")


def _strip_comments(text: str) -> str:
    """Drop GAMS comments: column-1 `*` lines and `$ontext`/`$offtext` blocks."""
    out: list[str] = []
    in_block = False
    for line in text.splitlines():
        low = line.strip().lower()
        if low.startswith("$offtext"):
            in_block = False
            continue
        if low.startswith("$ontext"):
            in_block = True
            continue
        if in_block:
            continue
        if line[:1] == "*":  # column-1 comment (GAMS rule)
            continue
        out.append(line)
    return "\n".join(out)


def _is_glob_stem(base: str, fragment: str) -> bool:
    """True if `base` appears as a family glob (`base_*` / `base*`) — a stem, not a
    real var (e.g. `pm_carbon_density_*`, `vm_cost_prod_*`). Mirrors the wildcard
    skip in check_gams_variables.filter_doc_vars."""
    return f"{base}_*" in fragment or f"{base}*" in fragment


def _cross_vars(fragment: str) -> set[str]:
    """Cross-module interface var bases (vm_/pm_/im_/pcm_/fm_) in a text fragment."""
    out: set[str] = set()
    for tok in GAMS_INTERFACE_RE.findall(fragment):
        base = strip_dims(tok)
        if CROSS_IFACE_RE.match(base) and is_interface_var(base) and not _is_glob_stem(base, fragment):
            out.add(base)
    return out


def _mask_ops(s: str) -> str:
    return _MASK_OPS_RE.sub(lambda m: "\x00" * len(m.group()), s)


def _classify_statement(stmt: str) -> tuple[set[str], set[str]]:
    """Return (populate_vars, read_vars) for one `;`-delimited GAMS statement.

    POPULATE = the leading identifier of the LHS, IFF it is a cross-iface var.
    Everything else (LHS conditions, RHS, equation header) = READ. Ambiguous
    statements (no equation `..`+relop, no bare `=`) contribute only READs, so a
    false POPULATE cannot be manufactured.
    """
    idx_dd = stmt.find("..")
    relm = REL_OP_RE.search(stmt)
    if idx_dd != -1 and relm and relm.start() > idx_dd:
        header = stmt[:idx_dd]
        body = stmt[idx_dd + 2:]
        rel2 = REL_OP_RE.search(body)
        lhs = body[: rel2.start()]
        rest = body[rel2.end():] + " " + header
    else:
        masked = _mask_ops(stmt)
        eqi = masked.find("=")
        if eqi == -1:
            return set(), _cross_vars(stmt)
        lhs = stmt[:eqi]
        rest = stmt[eqi + 1:]

    pop: set[str] = set()
    lead = _LEAD_ID_RE.match(lhs)
    if lead:
        base = strip_dims(lead.group(1))
        if CROSS_IFACE_RE.match(base) and is_interface_var(base):
            pop.add(base)
    read = (_cross_vars(lhs) | _cross_vars(rest)) - pop
    return pop, read


def build_role_map() -> tuple[dict[str, dict[str, set[str]]], dict[str, dict[str, set[str]]]]:
    """Return (role, realiz).

    role[var][modnum]   = subset of {"POPULATE","READ"} observed in code.
    realiz[var][modnum] = realization dir names in which the var was seen.
    Both keyed by 2-digit-ish module number strings (e.g. "10").
    """
    role: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    realiz: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    modules_root = MAGPIE_DIR / "modules"
    if not modules_root.is_dir():
        return role, realiz
    for module_dir in sorted(modules_root.iterdir()):
        if not module_dir.is_dir():
            continue
        mnum = module_dir.name.split("_", 1)[0]
        if not mnum.isdigit():
            continue
        for path in module_dir.rglob("*.gms"):
            rel_parts = path.relative_to(module_dir).parts
            realization = rel_parts[0] if len(rel_parts) > 1 else ""
            code = _strip_comments(read_text_or_empty(path))
            if not code:
                continue
            for stmt in code.split(";"):
                stmt = stmt.strip()
                if not stmt:
                    continue
                pop, rd = _classify_statement(stmt)
                for v in pop:
                    role[v][mnum].add("POPULATE")
                    if realization:
                        realiz[v][mnum].add(realization)
                for v in rd:
                    role[v][mnum].add("READ")
                    if realization:
                        realiz[v][mnum].add(realization)
    return role, realiz


def build_default_realization_by_modnum() -> dict[str, str]:
    """{modnum: default_realization} from config/default.cfg + dir suffixes."""
    modules_root = MAGPIE_DIR / "modules"
    cfg = MAGPIE_DIR / "config" / "default.cfg"
    suffix_to_num: dict[str, str] = {}
    if modules_root.is_dir():
        for d in modules_root.iterdir():
            if d.is_dir() and "_" in d.name and d.name.split("_", 1)[0].isdigit():
                num, suffix = d.name.split("_", 1)
                suffix_to_num[suffix] = num
    out: dict[str, str] = {}
    if cfg.is_file():
        for m in re.finditer(r"cfg\$gms\$(\w+)\s*<-\s*\"([^\"]+)\"", read_text_or_empty(cfg)):
            key, realz = m.group(1), m.group(2)
            if key in suffix_to_num:
                out[suffix_to_num[key]] = realz
    return out


def _multi_realization_modnums() -> set[str]:
    modules_root = MAGPIE_DIR / "modules"
    out: set[str] = set()
    if not modules_root.is_dir():
        return out
    for d in modules_root.iterdir():
        if not (d.is_dir() and "_" in d.name and d.name.split("_", 1)[0].isdigit()):
            continue
        reals = [c for c in d.iterdir() if c.is_dir() and c.name not in ("input", ".git")]
        if len(reals) > 1:
            out.add(d.name.split("_", 1)[0])
    return out


def _ref_any_nums() -> dict[str, set[str]]:
    """var -> set of module-number strings referencing it ANYWHERE (phantom denom)."""
    out: dict[str, set[str]] = {}
    for var, dirs in build_consumer_map().items():
        base = strip_dims(var)
        nums = {d.split("_", 1)[0] for d in dirs if "_" in d and d.split("_", 1)[0].isdigit()}
        out.setdefault(base, set()).update(nums)
    return out


# ---------------------------------------------------------------------------
# DOC SIDE — parse multi-module attribution triples
# ---------------------------------------------------------------------------

# Direction triggers, tested against a de-backticked line/clause.
READ_TRIGGER_RE = re.compile(
    r"consumers?\s+of|consumed\s+by|read\s+by|reads?\b|provided\s+to|provides?\s+to|"
    r"used\s+by|passed\s+to|feeds?\s+(?:into|to)|sent\s+to|supplies|downstream",
    re.IGNORECASE)
POP_TRIGGER_RE = re.compile(
    r"populated?\s+by|populates?|calculated?\s+by|calculates?|computed?\s+by|computes?|"
    r"written\s+by|writes?|produced?\s+by|produces?|provided?\s+by|supplied\s+by",
    re.IGNORECASE)
# Partial-list hedges: the doc is intentionally listing a subset -> suppress
# omissions (phantoms still flagged). Mirrors check_consumer_attribution D2.
# NOTE: punctuation-ending alternatives (e.g.) get NO trailing \b (a `.`->` `
# transition is not a word boundary, which silently killed the match).
HEDGE_RE = re.compile(
    r"\b(?:primary|main|most important|key consumers?|key downstream|principal|"
    r"among others|including|includes|broadly|broader|wider|touched by|for example|"
    r"such as|like|others?)\b|e\.?g\.|\betc\b", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*(```|~~~)")
# A continuation line that is a list item / bare NN_name list (used to gather the
# following list under a var-anchored header).
LIST_CONT_RE = re.compile(r"^\s*(?:[-*]\s|\d+\.\s|\d{1,2}_[a-z])")
# An explicit COMPLETENESS claim — the line asserts the FULL set for the var, so
# an omission is a genuine bug. Merely naming "Module N" is NOT completeness
# (that would bypass the ownership gate and reintroduce the shared-var FP).
COMPLETENESS_RE = re.compile(
    r"consumers?\s+of|\(\s*\d+\s+modules|these\s+modules|all\s+(?:consumers|readers|"
    r"producers|modules)|full\s+list|authoritative|complete\s+list", re.IGNORECASE)


# "Module(s) N, M, and P" enumeration — one verb, a comma/and list of numbers,
# EACH optionally followed by a "(label)". Real corpus forms:
#   module_52.md:484  "Consumers: Modules 14, 29, 30, ..."
#   module_12.md:878  "Module 13 (TC ...), 29 (cropland ...), 32 (...), ..."
MODULE_LIST_RE = re.compile(
    r"\bModules?\s+(\d{1,2}(?:\s*\([^)]*\))?(?:\s*(?:,|and|&)\s+\d{1,2}(?:\s*\([^)]*\))?)+)",
    re.IGNORECASE)


def _mod_nums(fragment: str) -> set[str]:
    """Distinct module NUMBER strings in a de-backticked fragment."""
    nums: set[str] = set()
    for m in MODULE_WORD_RE.finditer(fragment):
        nums.add(f"{int(m.group(1)):02d}")
    for m in MODNAME_RE.finditer(fragment):
        nums.add(f"{int(m.group(1)):02d}")
    for m in MODULE_LIST_RE.finditer(fragment):
        # Strip the "(label)" parentheticals first so a number inside a label
        # (e.g. "(within 5 years)") is not read as a module.
        grp = re.sub(r"\([^)]*\)", " ", m.group(1))
        for n in re.findall(r"\d{1,2}", grp):
            nums.add(f"{int(n):02d}")
    return nums


def _debacktick(s: str) -> str:
    return BACKTICK_TOKEN_RE.sub(" ", s)


def _cross_vars_backticked(line: str) -> list[str]:
    """Cross-iface var bases that appear INSIDE backticks on the line (dedup, ordered)."""
    out: list[str] = []
    for span in BACKTICK_TOKEN_RE.findall(line):
        for tok in GAMS_INTERFACE_RE.findall(span):
            base = strip_dims(tok)
            if (CROSS_IFACE_RE.match(base) and is_interface_var(base)
                    and not _is_glob_stem(base, span) and base not in out):
                out.append(base)
    return out


def parse_doc_triples(text: str) -> list[dict]:
    """Return attribution triples: {lineno, var, listed:set[str], direction, hedged, row}.

    direction in {"READ","POPULATE","UNKNOWN"}. Precision-first: only lines that
    name EXACTLY ONE backticked cross-iface var and carry a direction trigger are
    bound; for a var-anchored header ending in ':' / 'modules', the immediately
    following list lines (no new var) contribute their module numbers.
    """
    triples: list[dict] = []
    lines = text.splitlines()
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or HISTORICAL_RE.search(line):
            continue
        vars_here = [v for v in _cross_vars_backticked(line)]
        if len(vars_here) != 1:
            continue  # 0 or >1 vars on the line -> ambiguous binding -> skip
        deb = _debacktick(line)
        read_trig = READ_TRIGGER_RE.search(deb)
        pop_trig = POP_TRIGGER_RE.search(deb)
        if not (read_trig or pop_trig):
            continue
        if NEGATION_RE.search(deb):
            continue  # correct statement of absence, not an attribution
        var = vars_here[0]
        listed = _mod_nums(deb)
        # Var-anchored header: gather the following contiguous list (no new var).
        anchor = bool(line.rstrip().endswith(":") or COMPLETENESS_RE.search(deb))
        if anchor:
            for j in range(i + 1, min(len(lines), i + 8)):
                nxt = lines[j]
                if not nxt.strip():
                    break
                if _cross_vars_backticked(nxt):
                    break  # a new var starts a different binding
                if not LIST_CONT_RE.match(nxt):
                    break
                listed |= _mod_nums(_debacktick(nxt))
        if not listed:
            continue
        # Direction = the trigger NEAREST the first module mention (handles a mixed
        # line like "Writes `pm_x` (consumed by Module 14 ...)": the listed modules
        # sit next to "consumed by" -> READ, not to "Writes" -> POPULATE).
        direction = _pick_direction(read_trig, pop_trig, _first_module_pos(deb))
        triples.append({
            "lineno": i + 1, "var": var, "listed": listed, "direction": direction,
            "anchor": anchor, "hedged": bool(HEDGE_RE.search(deb)),
            "source": "prose", "row": line.strip()[:160],
        })
    return triples


def _first_module_pos(deb: str) -> int:
    positions = [m.start() for m in MODULE_WORD_RE.finditer(deb)]
    positions += [m.start() for m in MODNAME_RE.finditer(deb)]
    positions += [m.start() for m in MODULE_LIST_RE.finditer(deb)]
    return min(positions) if positions else 0


def _pick_direction(read_trig, pop_trig, ref_pos: int) -> str:
    if read_trig and not pop_trig:
        return "READ"
    if pop_trig and not read_trig:
        return "POPULATE"
    if not (read_trig or pop_trig):
        return "UNKNOWN"
    return "READ" if abs(read_trig.start() - ref_pos) <= abs(pop_trig.start() - ref_pos) else "POPULATE"


# --- Table forms ("Provides To (Outputs)" / "Receives From (Inputs)"). Each row
# is (module(s), var). Aggregate the listed modules PER VAR within a section, so
# a var with several rows keeps its full listed set. This is where the R54
# Module-58 omission actually hid (a "Provides To" table).
_TBL_SECTION_RE = re.compile(
    r"^\s{0,3}(?:#{1,6}|\*\*|-)?\s*.*?(provides\s+to|receives\s+from)\b", re.IGNORECASE)
_TBL_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
_TBL_SEP_RE = re.compile(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$")
_TBL_HEADER_CELL_RE = re.compile(
    r"^\s*\*{0,2}(module|to module|from module|source|target|consumer|producer|"
    r"variable|interface|receives|provides|from|to|use|file|desc)\b", re.IGNORECASE)


def parse_doc_table_triples(text: str) -> list[dict]:
    """Return attribution triples from Provides-To / Receives-From tables.

    direction: "Provides To" -> col-1 modules READ the var; "Receives From" ->
    col-1 modules POPULATE it. anchor=False (a table row is not, by itself, a
    completeness claim); the omission gate leans on ownership downstream.
    """
    triples: list[dict] = []
    lines = text.splitlines()
    in_table = armed = False
    direction: str | None = None
    acc: dict[str, dict] = {}

    def flush():
        for var, info in acc.items():
            triples.append({
                "lineno": info["line"], "var": var, "listed": info["modules"],
                "direction": info["dir"], "anchor": False, "hedged": False,
                "source": "table", "row": info["row"],
            })
        acc.clear()

    for i, line in enumerate(lines, start=1):
        sec = _TBL_SECTION_RE.match(line)
        if sec and "|" not in line:
            flush()
            armed, in_table = True, False
            direction = "READ" if "provides" in sec.group(1).lower() else "POPULATE"
            continue
        if _TBL_SEP_RE.match(line):
            if armed:
                in_table = True
            continue
        row = _TBL_ROW_RE.match(line)
        if not row:
            if line.strip() == "" or not line.lstrip().startswith("|"):
                flush()
                in_table = armed = False
            continue
        cells = [c.strip() for c in row.group(1).split("|")]
        if not cells:
            continue
        if _TBL_HEADER_CELL_RE.match(cells[0]):
            armed = True
            continue
        if not (in_table or armed) or len(cells) < 2 or direction is None:
            continue
        if HISTORICAL_RE.search(line) or NEGATION_RE.search(line):
            continue
        col1, col2 = cells[0], cells[1]
        mods = _mod_nums(col1)
        # A row may list SEVERAL vars in col-2 (consumer-perspective table: "M59
        # reads vm_land, pm_land_start, ..."). Bind the row's module(s) to EACH var
        # so per-var aggregation across the section is complete (missing this makes
        # a complete table look full of omissions).
        vars_c = _cross_vars_backticked(col2) or sorted(_cross_vars(col2))
        if not mods or not vars_c:
            continue
        for var in vars_c:
            info = acc.setdefault(var, {"modules": set(), "line": i, "dir": direction,
                                        "row": line.strip()[:160]})
            info["modules"] |= mods
    flush()
    return triples


# ---------------------------------------------------------------------------
# DIFF
# ---------------------------------------------------------------------------

SCAN_STATS = {"triples": 0, "docs_with_triples": 0, "unbound_docs": 0}


def diff_doc(text: str, rel_path: str, role, realiz, ref_any, producers,
             default_real, multi_real) -> tuple[list[dict], list[dict], int]:
    """Return (omissions, phantoms, triples_evaluated) for one doc."""
    fname = os.path.basename(rel_path)
    mod_m = re.search(r"module_(\d{1,2})", fname)
    doc_own = f"{int(mod_m.group(1)):02d}" if mod_m else None

    omissions: list[dict] = []
    phantoms: list[dict] = []
    triples = parse_doc_triples(text) + parse_doc_table_triples(text)
    for t in triples:
        var, listed, direction = t["var"], t["listed"], t["direction"]
        rolemap = role.get(var, {})
        read_nums = {m for m, r in rolemap.items() if "READ" in r}
        pop_nums = {m for m, r in rolemap.items() if "POPULATE" in r}
        role_any = read_nums | pop_nums
        declarer_dir = producers.get(var, "")
        declarer = declarer_dir.split("_", 1)[0] if "_" in declarer_dir else None
        exclude = {n for n in (declarer, doc_own) if n}

        # PHANTOM: listed module references the var nowhere in code (incl. comments).
        # Only for CLEANLY-BOUND triples — a table row (col1<->col2) or an explicit
        # anchor list. Non-anchor inline prose binds modules ambiguously (a "M16,
        # which feeds M17" transitive mention is not a claim about M17), and the
        # single-module / table phantom checkers already cover the clean cases.
        if t.get("source") == "table" or t.get("anchor"):
            refany = ref_any.get(var, set())
            for m in sorted(listed):
                if m in exclude:
                    continue
                if m not in refany:
                    phantoms.append({
                        "file": rel_path, "line": t["lineno"], "var": var,
                        "claimed_module": m, "row": t["row"],
                    })

        # OMISSION: a real member of the role set matching the direction, absent
        # from the list. Gated hard on CREDIBLE COMPLETENESS (omission over-flagging
        # is the primary failure mode). Only two credible cases:
        #   (1) an explicit var-anchored completeness header ("consumers of `V`
        #       (N modules): ...") — prose or wherever, direction as parsed;
        #   (2) a var's OWNER (declarer) listing its consumers in a Provides-To
        #       TABLE (source=table, direction=READ, doc_own==declarer) — this is
        #       exactly the R54 Module-58 class.
        # Everything else (partial provider rows for a shared var it doesn't own;
        # Receives-From producer lists; stray prose mentions) is PHANTOM-ONLY.
        if t["hedged"]:
            continue
        omission_ok = bool(t.get("anchor")) or (
            t.get("source") == "table" and direction == "READ"
            and doc_own is not None and doc_own == declarer
        )
        if not omission_ok:
            continue
        truth = read_nums if direction == "READ" else (pop_nums if direction == "POPULATE" else role_any)
        omitted = truth - listed - exclude
        for m in sorted(omitted):
            # Realization-scope: if m is multi-realization and references the var
            # ONLY in non-default realizations, tag low-confidence.
            confidence = "high"
            if m in multi_real:
                seen = realiz.get(var, {}).get(m, set())
                dflt = default_real.get(m)
                if dflt and seen and dflt not in seen:
                    confidence = "non-default-realization"
            omissions.append({
                "file": rel_path, "line": t["lineno"], "var": var,
                "omitted_module": m, "direction": direction,
                "confidence": confidence, "listed": sorted(listed), "row": t["row"],
            })

    SCAN_STATS["triples"] += len(triples)
    return omissions, phantoms, len(triples)


# ---------------------------------------------------------------------------
# Output / CLI
# ---------------------------------------------------------------------------

def _iter_docs():
    for doc in sorted(DOCS_DIR.glob("module_*.md")):
        if not doc.name.endswith("_notes.md"):
            yield doc
    if CROSS_DIR.is_dir():
        yield from sorted(CROSS_DIR.glob("*.md"))


def dump_rolemap(out_path: str | None) -> int:
    """Emit the code-derived ground-truth attribution map as JSON (LLM context)."""
    role, _ = build_role_map()
    producers = build_producer_map()
    payload: dict[str, dict] = {}
    for var, rolemap in role.items():
        payload[var] = {
            "declared_in": producers.get(var, "") or None,
            "populated_by": sorted({m for m, r in rolemap.items() if "POPULATE" in r}, key=int),
            "read_by": sorted({m for m, r in rolemap.items() if "READ" in r}, key=int),
        }
    blob = json.dumps(payload, indent=1, ensure_ascii=True, sort_keys=True)
    if out_path:
        Path(out_path).write_text(blob + "\n")
        print(f"{CHECK_NAME}: wrote role map for {len(payload)} interface vars -> {out_path}")
    else:
        print(blob)
    return 0


def main() -> int:
    args = sys.argv[1:]
    summary_only = "--summary-only" in args
    verbose = "--verbose" in args

    if "--dump-rolemap" in args:
        out = None
        if "--out" in args:
            out = args[args.index("--out") + 1]
        return dump_rolemap(out)

    modules_root = MAGPIE_DIR / "modules"
    if not modules_root.is_dir():
        print(f"{CHECK_NAME}: WARNING GAMS modules not found at {MAGPIE_DIR} - skipping.")
        return 0

    role, realiz = build_role_map()
    ref_any = _ref_any_nums()
    producers = build_producer_map()
    default_real = build_default_realization_by_modnum()
    multi_real = _multi_realization_modnums()

    all_om: list[dict] = []
    all_ph: list[dict] = []
    n_docs = 0
    for doc in _iter_docs():
        n_docs += 1
        rel = str(doc.relative_to(AGENT_DIR))
        before = SCAN_STATS["triples"]
        om, ph, ntrip = diff_doc(doc.read_text(encoding="utf-8", errors="ignore"),
                                  rel, role, realiz, ref_any, producers, default_real, multi_real)
        if ntrip:
            SCAN_STATS["docs_with_triples"] += 1
        all_om.extend(om)
        all_ph.extend(ph)

    # Coverage denominator ALWAYS printed (a "0" over few triples is BLIND).
    print(f"{CHECK_NAME}: coverage = {SCAN_STATS['triples']} multi-module attribution "
          f"triples across {SCAN_STATS['docs_with_triples']}/{n_docs} docs "
          f"(var-anchored lists + inline multi-module forms only).")
    print(f"{CHECK_NAME}: role map = {len(role)} interface vars; ref-any = {len(ref_any)}.")

    high = [o for o in all_om if o["confidence"] == "high"]
    ndr = [o for o in all_om if o["confidence"] != "high"]

    if all_ph:
        print(f"\n{CHECK_NAME}: {len(all_ph)} PHANTOM(s) (listed module references the var nowhere):")
        for f in (all_ph if not summary_only else all_ph[:20]):
            print(f"  {f['file']}:{f['line']}  `{f['var']}` lists M{f['claimed_module']} "
                  f"but it references the var nowhere. Line: {f['row']}")
    else:
        print(f"\n{CHECK_NAME}: 0 phantoms within covered triples.")

    if high:
        print(f"\n{CHECK_NAME}: {len(high)} OMISSION(s) [high-confidence] (real member absent from list):")
        for f in (high if not summary_only else high[:30]):
            print(f"  {f['file']}:{f['line']}  `{f['var']}` [{f['direction']}] omits M{f['omitted_module']} "
                  f"(code shows it {f['direction'].lower()}s the var). Line: {f['row']}")
    else:
        print(f"\n{CHECK_NAME}: 0 high-confidence omissions within covered triples "
              f"(NOT a corpus-clean claim — see coverage above).")

    if ndr and verbose:
        print(f"\n{CHECK_NAME}: {len(ndr)} omission(s) [non-default-realization — advisory]:")
        for f in ndr:
            print(f"  {f['file']}:{f['line']}  `{f['var']}` omits M{f['omitted_module']} "
                  f"(references only in a non-default realization).")

    print(f"\n{CHECK_NAME}: NOTE omissions are advisory + lower-confidence than phantoms; "
          f"confirm against develop + adversarial refute before any doc edit.")
    # Machine-greppable summary line (for validate_consistency.sh Check 34).
    print(f"{CHECK_NAME}: SUMMARY phantoms={len(all_ph)} omissions_high={len(high)} "
          f"omissions_advisory={len(ndr)} coverage_triples={SCAN_STATS['triples']}")
    return 0


# ---------------------------------------------------------------------------
# Hermetic self-test (fixture-first positive control)
# ---------------------------------------------------------------------------

def self_test() -> int:
    """Positive + negative controls with INJECTED code-side maps (no repo needed).

    Ground truth mirrors real fixtures. The headline positive control replicates
    the R54 'Module 58 absent' hider: vm_land_forestry is READ by {32,58}; a doc
    listing only {32} must flag 58 as an OMISSION.
    """
    ok = True
    # var -> modnum -> roles
    role = {
        "vm_land": {"10": {"POPULATE"}, "29": {"READ"}, "30": {"READ"}, "32": {"READ"},
                    "35": {"READ"}, "58": {"READ"}},
        "vm_land_forestry": {"32": {"POPULATE", "READ"}, "58": {"READ"}},
        "pm_carbon_density_ac": {"52": {"POPULATE"}, "14": {"READ"}, "35": {"READ"}},
        "vm_prod": {"17": {"POPULATE"}, "18": {"READ"}, "30": {"READ"}},
        "vm_tau": {"13": {"POPULATE"}, "14": {"READ"}},
    }
    realiz = {v: {m: {"only_dec18"} for m in role[v]} for v in role}
    ref_any = {v: set(role[v].keys()) for v in role}
    ref_any["vm_land"] |= {"11"}  # M11 mentions vm_land only in a comment -> ref_any but not role
    producers = {"vm_land": "10_land", "vm_land_forestry": "32_forestry",
                 "pm_carbon_density_ac": "52_carbon", "vm_prod": "17_production",
                 "vm_tau": "13_tc"}
    default_real: dict[str, str] = {}      # treat all as single-realization here
    multi_real: set[str] = set()

    def run(text, fname="modules/module_TEST.md"):
        SCAN_STATS["triples"] = 0
        return diff_doc(text, fname, role, realiz, ref_any, producers, default_real, multi_real)

    cases = []
    # POSITIVE 1 — the M58 hider: consumers-of header + list omits a real reader.
    cases.append((
        "pos-omission-m58",
        "**Direct consumers of `vm_land_forestry`** (1 module):\n- 32_forestry\n",
        {"omit": {("vm_land_forestry", "58")}, "phantom": set()},
    ))
    # POSITIVE 2 — var-anchored consumer list omits several real readers.
    cases.append((
        "pos-omission-list",
        "**Consumers of `vm_land`** (2 modules):\n- 29_cropland, 30_croparea\n",
        {"omit": {("vm_land", "32"), ("vm_land", "35"), ("vm_land", "58")}, "phantom": set()},
    ))
    # POSITIVE 3 — phantom: a listed module references the var nowhere.
    cases.append((
        "pos-phantom",
        "**Consumers of `vm_tau`**: Module 14 and Module 99.\n",
        {"omit": set(), "phantom": {("vm_tau", "99")}},
    ))
    # POSITIVE 4 — populate-direction omission.
    cases.append((
        "pos-populate-omission",
        "`pm_carbon_density_ac` is populated by Module 52.\n"
        "wait that is wrong, list should include the readers not populators\n",
        {"omit": set(), "phantom": set()},  # single populator listed, correct -> no omission
    ))
    cases.append((
        "pos-populate-omission-2",
        "**Provided by** modules populating `vm_prod`: Module 17.\n",
        {"omit": set(), "phantom": set()},  # 17 is the sole populator; correct
    ))
    # NEGATIVE 1 — complete consumer list -> no omission, no phantom.
    cases.append((
        "neg-complete",
        "**Consumers of `vm_land`** (5 modules):\n- 29_cropland, 30_croparea, 32_forestry, 35_natveg, 58_peatland\n",
        {"omit": set(), "phantom": set()},
    ))
    # NEGATIVE 2 — negation clause: correct absence, not a phantom/omission.
    cases.append((
        "neg-negation",
        "Module 99 is NOT a consumer of `vm_land`; it reads the aggregate instead.\n",
        {"omit": set(), "phantom": set()},
    ))
    # NEGATIVE 3 — partial-list hedge suppresses omissions (phantom still on).
    cases.append((
        "neg-hedge",
        "Key consumers of `vm_land` include e.g. Module 29 and Module 30.\n",
        {"omit": set(), "phantom": set()},
    ))
    # NEGATIVE 4 — historical wording skipped.
    cases.append((
        "neg-historical",
        "Previously the consumers of `vm_land` were listed as Module 29 (corrected R54).\n",
        {"omit": set(), "phantom": set()},
    ))
    # NEGATIVE 5 — fenced code skipped.
    cases.append((
        "neg-fence",
        "```\n**Consumers of `vm_land`**: Module 29\n```\n",
        {"omit": set(), "phantom": set()},
    ))
    # NEGATIVE 6 — >1 var on the line -> ambiguous binding -> skip.
    cases.append((
        "neg-multivar",
        "`vm_land` and `vm_prod` are both consumed by Module 29.\n",
        {"omit": set(), "phantom": set()},
    ))
    # NEGATIVE 7 — backticked realization path is not "Module 32".
    cases.append((
        "neg-backticked-realization",
        "**Consumers of `vm_land_forestry`** (`32_forestry/dynamic_may24`): Module 32, Module 58.\n",
        {"omit": set(), "phantom": set()},
    ))
    # NEGATIVE 8 — declarer/doc-own excluded (doc is module_10, vm_land declared in 10).
    cases.append((
        "neg-declarer-docown",
        "**Consumers of `vm_land`**: Module 29, 30, 32, 35, 58.\n",  # complete minus M10 (declarer/own)
        {"omit": set(), "phantom": set()},
        "modules/module_10.md",
    ))
    # POSITIVE 6 — TABLE form, the real R54 shape: a Provides-To table attributes a
    # forestry-specific var (owned by the doc's module) to M10 (phantom) and omits
    # its true sole consumer M58. Both a phantom AND an omission must fire.
    cases.append((
        "pos-table-m58",
        "#### Provides To (Outputs)\n"
        "| To Module | Variable | Use | File |\n"
        "| --- | --- | --- | --- |\n"
        "| **10_land** | vm_land_forestry | wrong: only M58 reads it | equations.gms:55 |\n",
        {"omit": {("vm_land_forestry", "58")}, "phantom": {("vm_land_forestry", "10")}},
        "modules/module_32.md",
    ))
    # NEGATIVE 9 — TABLE, a SHARED var the doc's module does NOT own: a partial
    # provider list is legitimate -> NO omission (ownership gate), and the listed
    # consumer is real -> NO phantom.
    cases.append((
        "neg-table-shared-var",
        "#### Provides To (Outputs)\n"
        "| To Module | Variable | Use | File |\n"
        "| --- | --- | --- | --- |\n"
        "| **29_cropland** | vm_land | forestry slice feeds land balance | equations.gms:55 |\n",
        {"omit": set(), "phantom": set()},
        "modules/module_32.md",
    ))

    for case in cases:
        label, text, expect = case[0], case[1], case[2]
        fname = case[3] if len(case) > 3 else "modules/module_TEST.md"
        om, ph, _ = run(text, fname)
        got_om = {(o["var"], o["omitted_module"]) for o in om if o["confidence"] == "high"}
        got_ph = {(p["var"], p["claimed_module"]) for p in ph}
        miss_om = expect["omit"] - got_om
        extra_om = got_om - expect["omit"]
        miss_ph = expect["phantom"] - got_ph
        extra_ph = got_ph - expect["phantom"]
        if not (miss_om or extra_om or miss_ph or extra_ph):
            print(f"  SELF-TEST PASS [{label}]")
        else:
            ok = False
            print(f"  SELF-TEST FAIL [{label}]: "
                  f"om_missing={sorted(miss_om)} om_extra={sorted(extra_om)} "
                  f"ph_missing={sorted(miss_ph)} ph_extra={sorted(extra_ph)}")

    # Coverage-counter sanity.
    SCAN_STATS["triples"] = 0
    run("**Consumers of `vm_land`**: Module 29\n")
    if SCAN_STATS["triples"] < 1:
        ok = False
        print("  SELF-TEST FAIL [coverage-counter]: evaluated 0 triples on a bound line")
    else:
        print("  SELF-TEST PASS [coverage-counter]")

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
