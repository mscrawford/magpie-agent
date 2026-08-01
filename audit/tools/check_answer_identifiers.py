#!/usr/bin/env python3
"""Mechanically detect FABRICATED identifiers in an assistant answer.

Why this exists
---------------
Phase 1A's grading layer was measured and found unreliable in BOTH directions: a
single Opus grader missed four outright falsehoods, two of which were pure
confabulations (a realization name that appears nowhere in the tree, and a grep
result reported from a directory that does not exist). Those two are not matters
of judgment -- they are decidable by `test -e`. This module makes that subset of
"is the answer false?" mechanical, so grader accuracy can be measured against a
key that no LLM produced.

Scope, stated honestly: this decides only the FABRICATION subclass. An answer can
be false in ways this cannot see (wrong role attribution between two identifiers
that both exist, a real path with a wrong line number, an omitted default
caveat). A clean report here is NOT "the answer is true"; it is "the answer names
nothing that fails to exist". Callers must not widen it.

Extraction, the existence oracle and the shared guards live in `magpie_corpus`
(2026-08-01 consolidation). What stays here is the PREDICATE: which combinations
of "extracted" and "does not exist" constitute a fabrication.

Usage
-----
  python3 check_answer_identifiers.py --selftest
  python3 check_answer_identifiers.py --batch <batch.md> --root <magpie-root> --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from magpie_corpus import (  # noqa: E402
    RE_CITED_LINES,
    RE_GAMS_IDENT,
    RE_GMS_PATH,
    RE_MODULE_DIR,
    RE_NEGATED,
    RE_REALIZATION_CTX,
    Tree,
    is_elided_path,
    is_glob_stem,
    is_negated,
    split_batch,
    window,
)

# Re-exported for callers that predate the consolidation (calibrate_graders.py,
# check_citation_content.py). Keep them importable from here.
__all__ = [
    "Corpus",
    "FABRICATION_KINDS",
    "RE_GAMS_IDENT",
    "RE_NEGATED",
    "check_answer",
    "split_batch",
]


class Corpus(Tree):
    """Existence oracle for this checker.

    A thin alias over the shared `Tree` -- the name is kept because
    `calibrate_graders.py` imports it.
    """


# --------------------------------------------------------------------------
# Checker
# --------------------------------------------------------------------------


def check_answer(text: str, corpus: Corpus) -> list[dict]:
    """Return a list of fabrication findings for one answer."""
    findings: list[dict] = []

    def emit(kind: str, token: str, span: tuple[int, int]) -> None:
        # The answer itself may be DENYING that the thing exists -- "there is no
        # module 50_nsoil_budget", "no `s80_solprint` scalar". Naming a
        # non-existent thing in order to say it does not exist is not a
        # fabrication. Three of seven false positives in the first real run were
        # this shape.
        if is_negated(text, span):
            return
        findings.append({
            "kind": kind,
            "token": token,
            "context": window(text, *span).strip()[:260],
        })

    for m in RE_MODULE_DIR.finditer(text):
        if not corpus.has_module(m.group(1)):
            emit("module_dir", m.group(1), m.span())

    for m in RE_GMS_PATH.finditer(text):
        p = m.group(1)
        if corpus.has_path(p):
            continue
        if is_elided_path(p):
            continue  # an explicitly elided path is not a claim about a filename
        # A path that is right except for the omitted realization level is a
        # CITATION defect, not a fabricated entity: the file does exist, one
        # directory down. Keep the classes apart -- conflating them was what let
        # "ambiguous" and "false" share a bucket in the first place.
        if corpus.path_exists_under_some_realization(p) or corpus.path_exists_at_module_level(p):
            emit("citation_imprecise", p, m.span())
        else:
            emit("gms_path", p, m.span())

    # A cited line number beyond the end of a real file cannot be right. This is
    # the one citation defect that needs no judgment at all.
    for m in RE_CITED_LINES.finditer(text):
        path, nums = m.group(1), m.group(2)
        n = corpus.line_count(path)
        if n is None:
            continue  # path handled by the gms_path check above
        over = [int(x) for x in re.findall(r"\d+", nums) if int(x) > n]
        if over:
            emit(
                "citation_out_of_range",
                f"{path}:{','.join(str(x) for x in over)} (file has {n} lines)",
                m.span(),
            )

    for m in RE_REALIZATION_CTX.finditer(text):
        tok = m.group(1) or m.group(2)
        if not tok:
            continue
        # Skip tokens that are obviously not realization names.
        if tok in {"the", "this", "default", "a", "its"}:
            continue
        # A GAMS identifier sitting next to the word "realization" is not a
        # realization name.
        if RE_GAMS_IDENT.fullmatch(tok) or corpus.has_identifier(tok):
            continue
        # Nor is a module name ("the `yields` realization" = module 14's
        # realization) or any other real token in the tree (`kbe60` is a set).
        if corpus.appears_anywhere(tok):
            continue
        if not corpus.has_realization(tok):
            emit("realization", tok, m.span())

    for m in RE_GAMS_IDENT.finditer(text):
        tok = m.group(1)
        # `vm_dem_*` is a glob the answer wrote; the regex sees the stem `vm_dem_`.
        if is_glob_stem(tok):
            continue
        # `vm_peatland` used as a grep stem for `vm_peatland_cost` is not an
        # invented name.
        if corpus.is_identifier_prefix(tok):
            continue
        if not corpus.has_identifier(tok):
            emit("identifier", tok, m.span())

    # De-duplicate on (kind, token): one finding per fabricated thing.
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for f in findings:
        k = (f["kind"], f["token"])
        if k in seen:
            continue
        seen.add(k)
        out.append(f)
    return out


# --------------------------------------------------------------------------
# Self-test: synthesized positives AND negatives, run BEFORE the corpus
# --------------------------------------------------------------------------

POSITIVES = [
    (
        "fabricated module dir",
        "I searched `modules/50_nsoil_budget/*/equations.gms` for vm_prod and the search returned no matches.",
        "module_dir",
        "50_nsoil_budget",
    ),
    (
        "fabricated realization",
        "Module 32 uses the `plant2forestry` realization to move land into plantations.",
        "realization",
        "plant2forestry",
    ),
    (
        "fabricated gms path",
        "This is implemented in modules/99_invented/default/equations.gms at line 12.",
        "gms_path",
        "modules/99_invented/default/equations.gms",
    ),
    (
        "fabricated identifier",
        "The model tracks this through `vm_totallyfakevariable` in the core.",
        "identifier",
        "vm_totallyfakevariable",
    ),
    (
        "cited line beyond end of a REAL file",
        "See modules/30_croparea/simple_apr24/equations.gms:99999 for the production identity.",
        "citation_out_of_range",
        "modules/30_croparea/simple_apr24/equations.gms:99999",
    ),
]

NEGATIVES = [
    ("real module dir", "Module 18_residues aggregates crop residues."),
    ("real realization", "The default realization is `flexreg_apr16` for module 18."),
    ("real gms path", "See modules/18_residues/flexreg_apr16/equations.gms:18."),
    (
        "REGRESSION: valid line number in a real file is not out of range",
        "The production identity is at modules/30_croparea/simple_apr24/equations.gms:15, "
        "and the residue link at modules/18_residues/flexreg_apr16/equations.gms:18,27.",
    ),
    ("real identifier", "The regional variable `vm_prod_reg` carries production."),
    (
        "negated fabrication is not a finding",
        "There is no module 50_nsoil_budget; the real directory is 50_nr_soil_budget.",
    ),
    # --- Regression negatives: every false positive from the first real run,
    # --- 2026-08-01, kept verbatim in shape so a future edit cannot reintroduce them.
    (
        "REGRESSION: glob stem is not an identifier",
        "Module 16 is the demand-side counterpart, reading/writing `vm_dem_*`/`vm_supply(i2,k)`.",
    ),
    (
        "REGRESSION: wrong name inside a negative claim",
        "Module 58 does not read forestry data from anywhere else "
        "(no separate `35_natural_vegetation` forest input for this state).",
    ),
    (
        "REGRESSION: identifier adjacent to the word realization",
        "`vm_land_forestry` is declared in module 32 (forestry), realization `dynamic_may24`.",
    ),
    (
        "REGRESSION: identifier before 'realization' in prose",
        "The `vm_land_forestry` variable itself is declared in module 32 (forestry realization).",
    ),
    (
        "REGRESSION: explicitly elided path is not a fabrication",
        "See `modules/40_transport/.../equations.gms:12` for the transport cost equation.",
    ),
    # --- Second batch of regression negatives: the 7 false positives found by
    # --- hand-adjudicating every flag from the 104-answer run, 2026-08-01.
    (
        "REGRESSION: module name used as realization (yields)",
        "Declared in `modules/14_yields/managementcalib_aug19/sets.gms:23` "
        "(default `yields` realization, `cfg$gms$yields <- \"managementcalib_aug19\"`).",
    ),
    (
        "REGRESSION: module name used as realization (bioenergy)",
        "The membership is identical across both realizations, so it does not depend "
        "on which `bioenergy` realization is configured.",
    ),
    (
        "REGRESSION: set name near the word realization (kbe60)",
        "This answer is realization-independent - `kbe60`'s membership and the "
        "`betr`/`begr` semantics are identical across all variants checked.",
    ),
    (
        "REGRESSION: negated identifier claim (s80_solprint)",
        "`magpie.solprint` is not a MAgPIE-namespaced switch (no `s80_solprint` scalar, "
        "no `cfg$gms$...solprint` config entry) - it is a native GAMS model attribute.",
    ),
    (
        "REGRESSION: negated identifier claim (s15_secondsolve)",
        "No `s15_secondsolve`-type switch exists; it is not an unconditional doubling, "
        "just two separate retry blocks.",
    ),
    (
        "REGRESSION: negated module dir (feed-from phrasing)",
        "No other module supplies forestry data to it (e.g., no separate feed from "
        "`35_natural_vegetation`).",
    ),
    (
        "REGRESSION: identifier stem used as a grep pattern (vm_peatland)",
        "Confirmed by grepping for `v58_`/`vm_peatland` under `modules/10_land/` "
        "and `modules/32_forestry/` (no hits).",
    ),
    (
        "REGRESSION: module.gms cited one level too deep",
        "Module 42 splits water demand into five sectors "
        "(`modules/42_water_demand/all_sectors_aug13/module.gms:10-11`).",
    ),
]

# Kinds that constitute a mechanically established FALSEHOOD. `citation_imprecise`
# is deliberately excluded: the cited file exists one directory down, so the claim
# is under-specified rather than false.
FABRICATION_KINDS = {"module_dir", "gms_path", "realization", "identifier"}


def selftest(corpus: Corpus) -> int:
    failures = 0
    print("== POSITIVE controls (must be flagged) ==")
    for name, text, kind, token in POSITIVES:
        got = check_answer(text, corpus)
        hit = any(f["kind"] == kind and token in f["token"] for f in got)
        print(f"  [{'PASS' if hit else 'FAIL'}] {name}: expected {kind}={token}")
        if not hit:
            failures += 1
            print(f"         got: {got}")

    # `citation_imprecise` is a legitimate finding on one negative (module.gms cited
    # a level too deep), so it is excluded here; an out-of-range line never is.
    strict = FABRICATION_KINDS | {"citation_out_of_range"}
    print("== NEGATIVE controls (must raise no FABRICATION / out-of-range) ==")
    for name, text in NEGATIVES:
        got = [f for f in check_answer(text, corpus) if f["kind"] in strict]
        ok = len(got) == 0
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            failures += 1
            print(f"         false positives: {got}")

    print(f"\nself-test: {failures} failure(s)")
    return failures


# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="magpie root (contains modules/)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--batch", help="batch.md with ### ANSWER <label> blocks")
    ap.add_argument("--json", help="write findings JSON here")
    a = ap.parse_args()

    corpus = Corpus(Path(a.root).resolve())
    print(
        f"corpus: {len(corpus.module_dirs)} modules, {len(corpus.realizations)} realizations, "
        f"{len(corpus.gms_paths)} .gms files, {len(corpus.identifiers)} identifiers",
        file=sys.stderr,
    )

    if a.selftest:
        return 1 if selftest(corpus) else 0

    if not a.batch:
        ap.error("need --batch or --selftest")

    answers = split_batch(Path(a.batch))
    result = {}
    for label, text in sorted(answers.items()):
        result[label] = check_answer(text, corpus)

    n_fab = sum(1 for v in result.values() if any(f["kind"] in FABRICATION_KINDS for f in v))
    n_cit = sum(1 for v in result.values() if any(f["kind"] == "citation_imprecise" for f in v))
    print(f"{n_fab}/{len(answers)} answers contain >=1 FABRICATED identifier")
    print(f"{n_cit}/{len(answers)} answers contain >=1 imprecise citation (separate class)")
    for label, fs in sorted(result.items()):
        for f in fs:
            tag = "FABRICATION" if f["kind"] in FABRICATION_KINDS else "citation"
            print(f"  {label}  {tag:<12} {f['kind']:<18} {f['token']}")

    if a.json:
        Path(a.json).write_text(json.dumps(result, indent=1))
        print(f"wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
