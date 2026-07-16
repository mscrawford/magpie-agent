#!/usr/bin/env python3
"""Slice-resolution layer: GAMS set-index intersection for advisory checkers.

WHY (see check_attribution_omissions.py's docstring, "KNOWN FP CLASS -- SLICE-
SCOPED CLAIMS"): the role maps used by check_attribution_omissions.py are
WHOLE-VARIABLE. A doc's consumer/producer claim is often scoped to ONE SLICE of
a shared interface variable (e.g. `vm_emissions_reg(i2,emis_oneoff,"co2_c")` is
a specific slice of `vm_emissions_reg`). A module can reference the VARIABLE
without touching the SLICE a doc is actually discussing -> a spurious
"omission" (the checker's one known FP class) or a wrong producer/consumer
direction claim (the `data_flow_direction` bug class). This module resolves
GAMS index tokens (quoted literals, named sets) to their member sets so a
caller can test whether two argument tuples for the SAME variable could
plausibly refer to overlapping slices.

WHAT THIS DOES NOT DO
  - No macro expansion: a `%compiletime_macro%` token is UNRESOLVED, never
    expanded to its configured value. Expanding it would require reading
    default.cfg / a specific scenario's cfg and is out of scope.
  - No alias resolution: `i2`/`j2`/`ac2`-style `alias(x,y)` targets are NEVER
    looked up back to their parent set. Aliases resolve to None (unresolved)
    even though the parent set (e.g. `i`) may itself be a fully known closed
    set. This is a deliberate simplification (see resolve_index docstring).
  - No dynamic/runtime set membership: sets populated at runtime via `SET(dom)
    = yes;` assignments (e.g. `ct(t)`, `h2(h)`) have no static `/ ... /` member
    list and resolve to None.
  - No relation/mapping-set flattening: a 2+-arity mapping set (e.g.
    `supreg(h,i)`, `emis_land(emis_oneoff,land,c_pools)`) is excluded from the
    index entirely (never resolved to a flat member list) -- see
    build_set_index docstring.

BINDING PRECISION RULE (governs slices_intersect -- see its docstring): a wrong
DISJOINT verdict would make a caller delete a real documented consumer, so
disjointness may ONLY be asserted from a dimension that resolves cleanly on
BOTH sides and empirically does not overlap. Any dimension that is unresolved
on exactly one side makes the whole comparison UNKNOWN (None), never False.
Callers MUST treat None as "fall back to whole-variable behaviour" -- this
module is strictly non-regressive by construction.

Usage:
  python3 scripts/gams_slices.py                 # print build_set_index() stats
  python3 scripts/gams_slices.py --self-test      # hermetic self-test
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_gams_variables import MAGPIE_DIR  # noqa: E402  (honours MAGPIE_DIR env override)
from check_set_members import parse_set_members  # noqa: E402  (reused, not rewritten)

# ---------------------------------------------------------------------------
# FILE 1a -- discover declared set names in a sets.gms body, then resolve each
# via the EXISTING parse_set_members(text, name).
# ---------------------------------------------------------------------------

# GAMS keywords that can start a declaration-block line but are never
# themselves a set name. Lower-cased comparison (GAMS keywords are
# conventionally lowercase in this codebase).
_SET_DECL_KEYWORDS = {
    "sets", "set", "alias", "table", "tables", "parameter", "parameters",
    "scalar", "scalars", "variable", "variables", "equation", "equations",
    "positive", "negative", "free", "binary", "integer", "model", "models",
    "option", "options", "display", "loop", "if", "else", "while", "execute",
    "singleton", "acronym", "acronyms", "file", "put", "solve",
}

# A candidate set-declaration line: identifier, optional `(domain)`, then some
# description text (requires the trailing `\s+\S` so a lone identifier with
# nothing after it -- e.g. a stray continuation token -- does not qualify).
_CANDIDATE_DECL_RE = re.compile(r"^\s*([a-zA-Z][a-zA-Z0-9_]*)\s*(\([^)]*\))?\s+\S")
# A line beginning with the `sets`/`set` keyword (inline form: `set NAME ...`).
_LEADING_KEYWORD_RE = re.compile(r"^\s*(sets|set)\b\s*", re.IGNORECASE)
# A standalone member-block delimiter `/`: counts UNLESS it has a word
# character (`\w` -- alnum/underscore) on BOTH sides, which is the shape of a
# `/` embedded inside a description (e.g. a unit like "tN/ha", guarded the
# same way parse_set_members guards it -- see its docstring). Real GAMS member
# blocks are routinely written with NO space adjoining one side of the slash
# -- `/member1,member2 /` (no space after the OPENER) and `/y1965,.../;` (no
# space before the CLOSER, immediately followed by punctuation) both occur in
# the real tree. Requiring whitespace on a SPECIFIC side (either side) desyncs
# the in/out-of-block state for the rest of the file: verified against
# modules/15_food/anthro_iso_jun22/sets.gms (`/underaged,working,retired /`,
# no space after the opener) and core/sets.gms (`.../y2010/;`, no space before
# the closer, glued straight to the terminating `;`). Requiring \w on neither
# side (this regex) handles both without losing the tN/ha guard.
_DELIM_SLASH_RE = re.compile(r"(?<!\w)/|/(?!\w)")

# Safety cap on a candidate's own text window (see build_set_index): bounds
# parse_set_members's search region so a set with NO member list of its own
# (e.g. a dynamic `ct(t)`) can never bleed into a much-later `/ ... /` block.
_MAX_WINDOW_LINES = 50


def _discover_set_names(text: str) -> list[tuple[str, int | None, int, int]]:
    """Return [(name, domain_arity_or_None, start_line, end_line), ...].

    `domain_arity` is the comma-count+1 of the `(...)` group if present, else
    None (a bare set with no domain). Lines are 0-based indices into
    `text.split("\\n")`. `end_line` is the EXCLUSIVE bound of this
    declaration's own text window: the next candidate's start line (or a
    `_MAX_WINDOW_LINES` cap, whichever is nearer) -- see module docstring for
    why an unbounded window is unsafe.

    A line is only tested as a candidate when NOT currently inside an odd-
    parity `/ ... /` member block (`in_block`), which is what correctly
    excludes multi-line block CONTENTS (e.g. a `NAME . (member)` mapping row,
    or a continuation line of a country-code list) from being mistaken for a
    sibling declaration -- those shapes would otherwise match
    `_CANDIDATE_DECL_RE` too.
    """
    lines = text.split("\n")
    # Comment-strip (column-1 `*`), same convention as parse_set_members, but
    # replace rather than drop so line indices used for windowing stay stable.
    clean = ["" if l.lstrip().startswith("*") else l for l in lines]

    raw: list[tuple[str, int | None, int]] = []  # (name, arity, start_line)
    in_block = False
    for idx, line in enumerate(clean):
        if not in_block:
            probe = line
            km = _LEADING_KEYWORD_RE.match(probe)
            if km:
                probe = probe[km.end():]
            cm = _CANDIDATE_DECL_RE.match(probe)
            if cm:
                name = cm.group(1)
                if name.lower() not in _SET_DECL_KEYWORDS:
                    domain = cm.group(2)
                    arity = domain.count(",") + 1 if domain else None
                    raw.append((name, arity, idx))
        for _ in _DELIM_SLASH_RE.finditer(line):
            in_block = not in_block

    out: list[tuple[str, int | None, int, int]] = []
    for i, (name, arity, start) in enumerate(raw):
        next_start = raw[i + 1][2] if i + 1 < len(raw) else len(clean)
        end = min(next_start, start + _MAX_WINDOW_LINES)
        out.append((name, arity, start, end))
    return out


def build_set_index(conflicts: list | None = None) -> dict[str, frozenset]:
    """Return {set_name: frozenset(members)} resolved from core/sets.gms AND
    every `<MAGPIE_DIR>/modules/*/*/sets.gms`.

    Only BARE sets (no domain) and SUBSET sets (single-parent domain, e.g.
    `poll58(pollutants)`) are resolved. A 2+-arity domain marks a
    RELATION/MAPPING set (e.g. `supreg(h,i)`) -- excluded entirely (never
    added to the index), matching resolve_index's "a mapping set -> None"
    contract: a name absent from the index resolves to None automatically.

    core/sets.gms is processed FIRST; on a name collision between core and a
    module-local set (or between two module-local sets) whose MEMBER SETS
    differ, core (or the first-seen file) wins and the collision is appended
    to `conflicts` (if given) rather than silently overwritten. An identical
    re-declaration (same members) is not treated as a conflict.
    """
    if conflicts is None:
        conflicts = []
    index: dict[str, frozenset] = {}
    origin: dict[str, str] = {}

    files: list[Path] = []
    core_sets = MAGPIE_DIR / "core" / "sets.gms"
    if core_sets.is_file():
        files.append(core_sets)
    modules_root = MAGPIE_DIR / "modules"
    if modules_root.is_dir():
        files.extend(sorted(modules_root.glob("*/*/sets.gms")))

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text:
            continue
        try:
            rel = str(path.relative_to(MAGPIE_DIR))
        except ValueError:
            rel = str(path)
        lines = text.split("\n")
        for name, arity, start, end in _discover_set_names(text):
            if arity is not None and arity > 1:
                continue  # relation/mapping set -- deliberately unresolved
            window = "\n".join(lines[start:end])
            members = parse_set_members(window, name)
            if not members:
                continue
            frozen = frozenset(m.lower() for m in members)
            if name in index:
                if index[name] != frozen:
                    conflicts.append({
                        "set": name,
                        "kept_from": origin[name],
                        "kept_members": sorted(index[name]),
                        "rejected_from": rel,
                        "rejected_members": sorted(frozen),
                    })
                continue  # first-seen wins (core processed first -> core wins)
            index[name] = frozen
            origin[name] = rel
    return index


# ---------------------------------------------------------------------------
# FILE 1b -- resolve one raw GAMS index token to its member set (or None).
# ---------------------------------------------------------------------------

_QUOTE_CHARS = "\"'"
# A compile-time macro substitution, `%NAME%` -- with or without surrounding
# quotes in the caller's raw token. UNRESOLVED regardless of quoting: the
# quotes make it look like a literal, but the content is a placeholder that
# expands to a config-dependent value we do not read here (see module
# docstring "WHAT THIS DOES NOT DO").
_MACRO_RE = re.compile(r"^%[^%]+%$")


def resolve_index(tok: str | None, set_index: dict[str, frozenset]) -> frozenset | None:
    """Resolve one raw GAMS index-position token to a frozenset of members.

    Returns None (UNRESOLVED) for anything this module does not have static,
    unambiguous ground truth for:
      - a compile-time macro (`%NAME%`, quoted or bare)
      - a token containing `$` (a `$`-conditional fragment)
      - an alias (`i2`, `j2`, `ac2`, ...) -- aliases are never in `set_index`
        (build_set_index only discovers `sets`/`set` declarations, never
        `alias(...)` statements), so this falls out of the plain lookup miss
        below without special-casing.
      - a mapping/relation set (excluded from `set_index` by construction)
      - any other identifier not found in `set_index`

    Resolves to a one-member frozenset for a quoted literal (`"peatland"` ->
    {peatland}), or to the full member frozenset for a bare token that matches
    a known set name in `set_index` (`emis_oneoff` -> its declared members;
    `land` -> the full `land` set, since an unquoted named-set argument in a
    GAMS call restricts/iterates that whole set, not one element of it).
    """
    if tok is None:
        return None
    t = tok.strip()
    if not t:
        return None
    if "$" in t:
        return None
    if len(t) >= 2 and t[0] == t[-1] and t[0] in _QUOTE_CHARS:
        inner = t[1:-1]
        if _MACRO_RE.match(inner):
            return None
        return frozenset({inner.lower()})
    if _MACRO_RE.match(t):
        return None
    if t in set_index:
        return set_index[t]
    return None


# ---------------------------------------------------------------------------
# FILE 1c -- do two resolved argument tuples plausibly refer to the same slice?
# ---------------------------------------------------------------------------

def slices_intersect(a: tuple, b: tuple) -> bool | None:
    """True | False | None for two resolved argument tuples of the SAME var.

    `a`/`b` are tuples of per-dimension `frozenset(members)` or None (as
    produced by resolve_index over each raw index token, in order).

    Different arities (dimension counts) -> None (not comparable at all).

    Per dimension, classify:
      - BOTH None (symmetric-unresolved, e.g. the same alias `i2` used as the
        region loop variable on both sides): ignored -- neither proves overlap
        nor disjointness. This is what lets e.g. two `vm_emissions_reg(i2,...)`
        calls be compared at all despite neither side resolving the region
        dimension.
        KNOWN GAP (accepted; low harm): this bucket does NOT verify that the two
        unresolved tokens are the SAME symbol. Two DIFFERENT unresolved tokens
        (say macro "%A%" vs macro "%B%") land here too and are ignored, so a pair
        that is genuinely disjoint on that axis can come back True. The harm
        direction is safe -- this yields a MISSED disjointness (false negative),
        never a false DISJOINT -- and the dominant real case is domain aliases
        (i2/j2/t), which genuinely are the same symbol on both sides. To close it,
        resolve_index would have to return a sentinel carrying the raw token so
        this branch could compare tokens for equality.
      - EXACTLY ONE None (asymmetric: one side has real evidence, the other is
        a total unknown -- e.g. a compile-time macro compared against a
        resolved literal): the unknown side could turn out to be anything,
        including a match or a genuine miss, so this dimension can never
        prove disjointness NOR complete a full intersection proof -> marks the
        whole comparison AMBIGUOUS.
      - BOTH resolved: compute actual set overlap. An EMPTY overlap on any
        single such dimension proves the whole tuple pair disjoint --
        REGARDLESS of any other dimension's resolution status (a Cartesian
        product of slices is empty as soon as ANY one axis's projections don't
        overlap; other axes cannot rescue it). This is why a DISJOINT dimension
        overrides everything else, immediately, on the spot.

    Final verdict:
      - ANY dimension proven disjoint -> False (checked first: dispositive).
      - ELSE, if any dimension was ambiguous (exactly-one-side-unresolved)
        -> None (cannot certify full intersection; cannot rule out disjoint
        either).
      - ELSE (every dimension is either both-resolved-and-overlapping, or
        symmetric-unresolved) -> True.
    """
    if len(a) != len(b):
        return None
    ambiguous = False
    for da, db in zip(a, b):
        if da is None and db is None:
            continue
        if da is None or db is None:
            ambiguous = True
            continue
        if not (da & db):
            return False
    return None if ambiguous else True


# ---------------------------------------------------------------------------
# Self-test (hermetic -- injected set index / synthetic sets.gms text only)
# ---------------------------------------------------------------------------

def self_test() -> int:
    ok = True

    def check(label, got, expect):
        nonlocal ok
        if got == expect:
            print(f"  SELF-TEST PASS [{label}]: got {got!r}")
        else:
            ok = False
            print(f"  SELF-TEST FAIL [{label}]: expected {expect!r}, got {got!r}")

    # --- resolve_index, injected set_index (no repo needed) -----------------
    set_index = {
        "emis_oneoff": frozenset({"crop_vegc", "crop_litc", "past_vegc"}),
        "emis_source": frozenset({"crop_vegc", "crop_litc", "past_vegc", "inorg_fert", "peatland"}),
        "pollutants_maccs57": frozenset({"ch4", "n2o_n_direct"}),
        "poll58": frozenset({"co2_c", "ch4", "n2o_n_direct"}),
        "land": frozenset({"crop", "past", "forestry", "primforest", "secdforest", "urban", "other"}),
        "c_pools": frozenset({"vegc", "litc", "soilc"}),
    }

    check("quoted literal", resolve_index('"peatland"', set_index), frozenset({"peatland"}))
    check("quoted literal (single-quote)", resolve_index("'co2_c'", set_index), frozenset({"co2_c"}))
    check("known set name", resolve_index("poll58", set_index), set_index["poll58"])
    check("macro (quoted)", resolve_index('"%c56_carbon_stock_pricing%"', set_index), None)
    check("macro (bare)", resolve_index("%c56_carbon_stock_pricing%", set_index), None)
    check("alias (unknown identifier)", resolve_index("i2", set_index), None)
    check("dollar-conditional token", resolve_index("t$active", set_index), None)
    check("unknown bare identifier", resolve_index("j2", set_index), None)

    # --- slices_intersect: the four MANDATORY controls ----------------------
    # Positive: provably-disjoint pair (both dims resolve on both sides; one
    # dimension's member sets are disjoint).
    disjoint_pair = (
        (None, frozenset({"co2_c"})),
        (None, frozenset({"ch4", "n2o_n_direct"})),
    )
    check("MANDATORY positive: disjoint -> False",
          slices_intersect(disjoint_pair[0], disjoint_pair[1]), False)

    # Positive: intersecting pair (some dims resolve+overlap, none disjoint).
    intersecting_pair = (
        (None, frozenset({"peatland"}), frozenset({"co2_c", "ch4", "n2o_n_direct"})),
        (None, frozenset({"crop_vegc", "peatland", "inorg_fert"}), frozenset({"ch4", "n2o_n_direct"})),
    )
    check("MANDATORY positive: intersecting -> True",
          slices_intersect(intersecting_pair[0], intersecting_pair[1]), True)

    # NEGATIVE (critical): a pair with an UNRESOLVED (asymmetric) dimension,
    # and NO other dimension disjoint -> must be None, NEVER False.
    ambiguous_pair = (
        (frozenset({"crop"}), None),
        (frozenset({"crop", "past"}), frozenset({"actual"})),
    )
    check("MANDATORY negative (critical): asymmetric-unresolved dim -> None (never False)",
          slices_intersect(ambiguous_pair[0], ambiguous_pair[1]), None)

    # Negative: differing arity -> None.
    check("MANDATORY negative: differing arity -> None",
          slices_intersect((frozenset({"a"}),), (frozenset({"a"}), frozenset({"b"}))), None)

    # --- extra regression guards ---------------------------------------------
    # An unresolved dim must not be able to MANUFACTURE a False even when it is
    # the only dim examined (symmetric case: both None -> ignored -> True by
    # default, since nothing contradicts and nothing was asked to be proven).
    check("both-sides-unresolved single dim -> True (nothing contradicts)",
          slices_intersect((None,), (None,)), True)
    # A disjoint dimension must win even when ANOTHER dimension is ambiguous
    # (mirrors CONTROL A's shape: one unresolved dim + one disjoint dim).
    disjoint_plus_ambiguous_a = (None, frozenset({"co2_c"}), frozenset({"crop"}))
    disjoint_plus_ambiguous_b = (None, frozenset({"ch4"}), None)
    check("disjoint dim overrides an ambiguous dim -> False",
          slices_intersect(disjoint_plus_ambiguous_a, disjoint_plus_ambiguous_b), False)

    # --- _discover_set_names / build_set_index, hermetic synthetic sets.gms -
    synthetic = (
        "sets\n"
        "\n"
        "  emis_source_inorg_fert_n2o(emis_source) subset inorg_fert_n2o emissions\n"
        "  /inorg_fert, resid, som/\n"
        "\n"
        "  pollutants_maccs57(pollutants) pollutants via which MAC costs are calculated\n"
        "  / ch4, n2o_n_direct /\n"
        "\n"
        "  set ct(t) Current time period;\n"
        "\n"
        "  emis_land(emis_oneoff,land,c_pools) Mapping between land and carbon pools\n"
        "  /crop_vegc . (crop) . (vegc)/\n"
        "\n"
        ";\n"
        "\n"
        "alias(t,t2);\n"
    )
    names = _discover_set_names(synthetic)
    name_set = {n for n, _a, _s, _e in names}
    check("discovery: finds pollutants_maccs57 + emis_source_inorg_fert_n2o",
          {"pollutants_maccs57", "emis_source_inorg_fert_n2o"} <= name_set, True)
    check("discovery: does NOT register 'sets'/'alias' as a name",
          bool({"sets", "alias", "set"} & name_set), False)
    check("discovery: registers 'ct' as a candidate (arity=1) with no members",
          any(n == "ct" and a == 1 for n, a, _s, _e in names), True)
    check("discovery: 'emis_land' has arity 3 (mapping, to be excluded upstream)",
          any(n == "emis_land" and a == 3 for n, a, _s, _e in names), True)

    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="gams_slices_selftest_")
    try:
        core_dir = Path(tmp) / "core"
        core_dir.mkdir()
        (core_dir / "sets.gms").write_text(synthetic)
        mod_dir = Path(tmp) / "modules" / "99_test" / "on"
        mod_dir.mkdir(parents=True)
        # A module-local set.gms with a genuine collision (different members
        # under the same name) AND a clean duplicate (same members).
        (mod_dir / "sets.gms").write_text(
            "sets\n"
            "  pollutants_maccs57 wrongly redeclared with different members\n"
            "  / ch4, co2_c /\n"
            "\n"
            "  poll58(pollutants) Wetland emissions that can be taxed\n"
            "  / co2_c, ch4, n2o_n_direct /\n"
            ";\n"
        )
        global MAGPIE_DIR
        saved = MAGPIE_DIR
        MAGPIE_DIR = Path(tmp)
        try:
            conflicts: list = []
            idx = build_set_index(conflicts)
        finally:
            MAGPIE_DIR = saved
        check("build_set_index: resolves pollutants_maccs57 from core",
              idx.get("pollutants_maccs57"), frozenset({"ch4", "n2o_n_direct"}))
        check("build_set_index: resolves poll58 from module sets.gms",
              idx.get("poll58"), frozenset({"co2_c", "ch4", "n2o_n_direct"}))
        check("build_set_index: 'ct' (no member list) is absent from the index",
              "ct" in idx, False)
        check("build_set_index: 'emis_land' (mapping, arity 3) is absent from the index",
              "emis_land" in idx, False)
        check("build_set_index: core wins the pollutants_maccs57 collision (exposed, not silent)",
              (idx.get("pollutants_maccs57") == frozenset({"ch4", "n2o_n_direct"})
               and any(c["set"] == "pollutants_maccs57" for c in conflicts)),
              True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("gams_slices self-test: PASS")
        print("SELFTEST_OK gams_slices")
        return 0
    print("gams_slices self-test: FAIL")
    return 1


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    conflicts: list = []
    idx = build_set_index(conflicts)
    print("gams_slices: set-index build")
    print("=============================")
    print(f"MAGPIE_DIR: {MAGPIE_DIR}")
    print(f"Resolved sets: {len(idx)}")
    if conflicts:
        print(f"Name collisions (exposed, first-seen kept): {len(conflicts)}")
        for c in conflicts:
            print(f"  {c['set']}: kept from {c['kept_from']} {c['kept_members']}, "
                  f"rejected from {c['rejected_from']} {c['rejected_members']}")
    else:
        print("Name collisions: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
