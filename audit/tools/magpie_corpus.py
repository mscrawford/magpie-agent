#!/usr/bin/env python3
"""Shared extraction primitives and existence oracle for the audit checkers.

Why this module exists
----------------------
Three checkers grew independently, and each rolled its own identifier extractor:

  check_answer_identifiers.py   fabricated names in an answer
  check_citation_content.py     does a cited file:line contain what it is cited for
  check_default_realization.py  a non-default realization described without saying so

By 2026-08-01 the duplication was measurable, not theoretical:

  * the GAMS prefix alternation `(?:vm|pm|fm|sm|...)_` was written out **twice**,
    character for character, in two files. Adding a prefix to one would have
    silently diverged the other with no test able to see it.
  * the module/realization tree was walked **three times** under three slightly
    different definitions of "realization" (one counted `modules/NN_x/input/` as
    one, two did not).
  * the same false-positive classes were fixed **per checker, after being
    rediscovered per checker**: the trailing-underscore glob stem (`vm_dem_`)
    was found and patched separately in two files, with a comment in each
    pointing at the other.

That last line is the actual cost. A guard learned in one checker did not reach
the others until the same false positive was paid for again.

The trade this makes, stated plainly
------------------------------------
Consolidation converts three INDEPENDENT extractors into one SHARED one. That
removes divergence, and in exchange a defect here is now CORRELATED across all
three checkers -- the failure mode gets rarer but wider. The compensating control
is that this module carries its own positive and negative controls
(`--selftest`), rather than being tested only through its callers. Run them: a
dead check passes its negatives vacuously, which has happened in this repo.

What is deliberately NOT shared
-------------------------------
Predicates. Each checker asks a different question, and a guard that is correct
for one can be wrong for another:

  * `is_identifier_prefix` (treat `vm_peatland` as a stem of `vm_peatland_cost`)
    is essential to the fabrication checker and would REDUCE RECALL in the
    citation checker, which matches identifiers as substrings of a line and so
    already resolves a stem against its full name.
  * The citation checker matches identifiers by SUBSTRING; the default-realization
    checker deliberately matches on IDENTIFIER BOUNDARIES, because module 80's
    default `nlp_apr17` is a substring of the non-default `lp_nlp_apr17` and a
    containment test excuses exactly the reference it exists to catch.

So: extraction and existence are shared, judgment is not.

Usage
-----
  python3 magpie_corpus.py --selftest --root <magpie-root>
"""

from __future__ import annotations

import argparse
import re
import sys
from functools import cached_property
from pathlib import Path

# ==========================================================================
# Regex primitives -- each defined EXACTLY ONCE
# ==========================================================================

# GAMS identifier prefixes used in MAgPIE (interface + module-local).
#
# Written once, as a string, and interpolated everywhere it is needed. This is
# the specific duplication that motivated the module: the alternation used to be
# spelled out verbatim in two files.
GAMS_PREFIX_ALT = (
    r"vm|pm|fm|sm|im|om|xm|q\d{2}|v\d{2}|p\d{2}|s\d{2}|c\d{2}|i\d{2}|f\d{2}|o\d{2}|x\d{2}"
)

RE_GAMS_IDENT = re.compile(rf"\b((?:{GAMS_PREFIX_ALT})_[a-z][A-Za-z0-9_]*)\b")

# A MAgPIE module directory: two digits, underscore, lowercase name.
RE_MODULE_DIR = re.compile(r"\b(\d{2}_[a-z][a-z0-9_]*)\b")

# A .gms path rooted at modules/ or core/.
RE_GMS_PATH = re.compile(r"\b((?:modules|core)/[A-Za-z0-9_./-]+\.gms)\b")

# A cited .gms path WITH line numbers: `modules/x/y.gms:12`, `:12,17`, `:12-14`.
RE_CITED_LINES = re.compile(
    r"\b((?:modules|core)/[A-Za-z0-9_./-]+\.gms):(\d+(?:\s*[-,]\s*\d+)*)"
)

# The citation checker resolves a wider set than the fabrication checker: it also
# accepts `config/default.cfg:811`. Kept as a SEPARATE name rather than widening
# RE_CITED_LINES, because widening would change what the fabrication checker
# range-checks, and that is a scope change, not a consolidation.
RE_CITATION = re.compile(
    r"\b((?:modules|core|config)/[A-Za-z0-9_./-]+\.(?:gms|cfg)):(\d+(?:\s*[-,]\s*\d+)*)"
)

# `modules/18_residues/flexcluster_jul23/...` -- (module dir, realization dir).
RE_REAL_PATH = re.compile(r"\bmodules/(\d{2}_[a-z][a-z0-9_]*)/([A-Za-z][A-Za-z0-9_]*)\b")

# A backticked token near the word "realization"/"realisation".
#
# Both directions are needed: the real fabrication this was built to catch
# ("in the `plant2forestry` realization") is the BACKWARD form. But the backward
# form also produced 2 of 6 false positives by reaching across a clause to a
# variable name. The backward window is therefore tight (<=12 chars, i.e.
# "the `X` realization") while the observed false positives sat 38 and 51 chars
# away.
RE_REALIZATION_CTX = re.compile(
    r"reali[sz]ation[^.\n]{0,60}?`([A-Za-z][A-Za-z0-9_]*)`"
    r"|`([A-Za-z][A-Za-z0-9_]*)`[^.\n]{0,12}?reali[sz]ation",
    re.IGNORECASE,
)

# A bare realization name in prose (`flexcluster_jul23`), not a path. Restricted
# to the dated MAgPIE naming convention on purpose: undated names like `static`,
# `off` and `exo` are ordinary English and would false-positive everywhere.
RE_DATED_REALIZATION = re.compile(
    r"\b([a-z][a-z0-9_]*_(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\d{2})\b"
)

# An equation definition: `q30_prod(j2,kcr) ..` -- occurs exactly once per file,
# which is what makes it usable as a STRUCTURAL anchor.
RE_EQN_DEF = re.compile(r"^\s*(q\d{2}_[A-Za-z0-9_]+)\s*(\([^)]*\))?\s*\.\.")

RE_CFG_KEY = re.compile(r'cfg\$gms\$([A-Za-z_][A-Za-z0-9_]*)\s*<-\s*"([^"]+)"')


# ==========================================================================
# Guards -- learned once, available to every checker
# ==========================================================================

# An assertion that something does NOT exist is not a fabrication.
# "no separate `35_natural_vegetation` input" names a wrong identifier while
# claiming it is NOT used -- the claim's truth does not rest on the name existing.
RE_NEGATED = re.compile(
    r"(?:does not exist|doesn't exist|no such|not a real|is not present|"
    r"there is no|no module|not found in the tree|does not appear anywhere|"
    r"\bno\s+(?:separate\s+|other\s+)?`?[A-Za-z0-9_]*`?\s*(?:forest\s+)?input|"
    r"does not read|not read from)",
    re.IGNORECASE,
)

# A bare negation cue. Applied to a SHORT left window only: three of seven false
# positives in the first real run were "no `s80_solprint` scalar" / "no separate
# feed from `35_natural_vegetation`", where the cue sits immediately to the left.
RE_NEG_CUE = re.compile(r"\b(?:no|not|never|neither|nonexistent|non-existent)\b", re.IGNORECASE)

NEG_LEFT_WINDOW = 40      # chars to the left scanned for a bare negation cue
NEG_ADJACENT_WINDOW = 12  # the tighter window used when judging a NAMED claim
CTX_PAD = 90              # chars either side used as the reported/searched context


def window(text: str, start: int, end: int, pad: int = CTX_PAD) -> str:
    """Context slice around a match, newlines flattened."""
    return text[max(0, start - pad) : min(len(text), end + pad)].replace("\n", " ")


def is_negated(text: str, span: tuple[int, int], pad: int = CTX_PAD) -> bool:
    """True if the surrounding prose DENIES the thing exists.

    Two tests, both learned from real false positives:
      1. an explicit non-existence phrase anywhere in the +/-pad context;
      2. a bare negation cue in the short left window ("no `s80_solprint`").
    """
    if RE_NEGATED.search(window(text, span[0], span[1], pad)):
        return True
    return bool(RE_NEG_CUE.search(text[max(0, span[0] - NEG_LEFT_WINDOW) : span[0]]))


def is_negated_claim(clause: str, tokens: list[str]) -> bool:
    """True if `clause` DENIES the existence of EVERY token in `tokens`.

    For a caller that has already isolated a clause and knows which identifiers
    the clause is about (the citation checker). Anchored per token, deliberately:
    a first version tested the whole clause for a bare negation cue, and
    "`vm_fake` is NOT optional and is defined at ...:15" then read as a denial,
    silently deleting a real mis-citation. A recall hole does not announce
    itself, so the cue has to attach to the token it supposedly negates.

    Requires ALL tokens to be denied: if the clause asserts even one identifier
    positively, the citation is making a positive claim and must be checked.

    Negation binds within a SUB-clause. "There is no `vm_fake`, but `vm_prod_reg`
    is defined here" denies only the first; testing a +/-90 character window
    around each token let the leading "there is no" reach across the comma and
    suppress both. So the clause is cut on `,` / `;` and each token is judged
    inside its own piece.

    The bare-cue window is also TIGHTER here than in `is_negated` (12 chars, not
    40): "not solved for) every timestep in `presolve.gms`" put a "not" 36
    characters from a token it does not modify, which is enough to suppress a
    finding that should have been checked.
    """
    if not tokens:
        return False
    pieces = re.split(r"[,;]", clause)
    for tok in tokens:
        for piece in pieces:
            i = piece.find(tok)
            if i == -1:
                continue
            denied = bool(
                RE_NEGATED.search(window(piece, i, i + len(tok)))
                or RE_NEG_CUE.search(piece[max(0, i - NEG_ADJACENT_WINDOW): i])
            )
            if denied:
                break            # this token is denied; check the next one
            return False         # asserted positively -> the claim is positive
        else:
            return False         # token not located in any piece
    return True


def is_glob_stem(tok: str) -> bool:
    """`vm_dem_*` is a glob the answer wrote; the regex sees the stem `vm_dem_`.

    A trailing underscore is never a real identifier. This guard was discovered
    twice -- once per checker -- before this module existed.
    """
    return tok.endswith("_")


def is_elided_path(p: str) -> bool:
    """`modules/40_transport/.../equations.gms` is an explicit elision, not a
    claim about a filename."""
    return "..." in p


SOURCE_EXTENSIONS = (".gms", ".cfg", ".md", ".json", ".csv")


def is_filename(tok: str) -> bool:
    """`presolve.gms` names a LOCATION, not something inside a file.

    The same rule as the directory-name guard, one level down. A file almost
    never contains its own basename, so admitting `presolve.gms` as a "claimed
    identifier" guarantees a spurious "identifier absent from the cited file".
    Found 2026-08-01 while adjudicating the consolidation diff: the finding was
    being suppressed only by an incidental "not" 36 characters away, i.e. right
    outcome, wrong mechanism -- and a mechanism that would delete real findings
    elsewhere.
    """
    return tok.endswith(SOURCE_EXTENSIONS)


def split_batch(path: Path) -> dict[str, str]:
    """Split a batch.md of '### ANSWER <label>' blocks into {label: text}."""
    raw = path.read_text(errors="ignore")
    parts = re.split(r"^### ANSWER\s+(\S+)\s*$", raw, flags=re.MULTILINE)
    out: dict[str, str] = {}
    for i in range(1, len(parts) - 1, 2):
        out[parts[i].strip()] = parts[i + 1]
    return out


# ==========================================================================
# Existence oracle
# ==========================================================================

# `modules/NN_x/input/` holds source data, not a realization.
NON_REALIZATION_DIRS = {"input"}

# Files a citation may be resolved against.
ALLOWED_PREFIXES = ("modules/", "core/", "config/")


class Tree:
    """One walk of the MAgPIE tree, serving every checker.

    Cheap facts (directory structure, config defaults) are computed eagerly in
    __init__. Everything that requires READING file contents -- the identifier
    set, the word set, per-file lines -- is lazy, so the default-realization
    checker, which needs no file contents at all, pays nothing for them.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        mod_root = self.root / "modules"
        if not mod_root.is_dir():
            raise SystemExit(f"no modules/ under {self.root}")

        self.module_dirs: set[str] = set()
        self.module_names: set[str] = set()          # "14_yields" -> "yields"
        self.realizations_by_module: dict[str, set[str]] = {}
        self._all_subdirs: set[str] = set()          # incl. `input`, for dir_names

        for m in sorted(mod_root.iterdir()):
            if not m.is_dir():
                continue
            self.module_dirs.add(m.name)
            if "_" in m.name:
                self.module_names.add(m.name.split("_", 1)[1])
            subs = {r.name for r in m.iterdir() if r.is_dir()}
            self._all_subdirs |= subs
            self.realizations_by_module[m.name] = subs - NON_REALIZATION_DIRS

        # config/default.cfg: `cfg$gms$yields <- "managementcalib_aug19"`.
        self.defaults_by_module: dict[str, str] = {}
        self._cfg_text = ""
        cfg = self.root / "config" / "default.cfg"
        if cfg.is_file():
            self._cfg_text = cfg.read_text(errors="ignore")
            keys = dict(RE_CFG_KEY.findall(self._cfg_text))
            for mod in self.module_dirs:
                short = mod.split("_", 1)[1] if "_" in mod else mod
                if short in keys:
                    self.defaults_by_module[mod] = keys[short]

        self._lines_cache: dict[str, list[str] | None] = {}
        self._spans_cache: dict[str, dict[str, tuple[int, int]]] = {}
        self._linecounts: dict[str, int] = {}

    # ---- directory-level facts (eager) -----------------------------------

    @cached_property
    def realizations(self) -> set[str]:
        """Flat set of realization names across all modules."""
        out: set[str] = set()
        for v in self.realizations_by_module.values():
            out |= v
        return out

    @cached_property
    def dir_names(self) -> set[str]:
        """Every token that names a LOCATION rather than file content.

        Deliberately WIDER than `realizations`: it keeps `input` and includes
        module directory names and their short forms. A citation checker uses
        this to reject "claimed identifiers" that are really directory names --
        they can never appear inside the cited file's text. Treating them as
        claimed identifiers produced 7 of 7 false positives in the 2026-08-01
        stratified precision sample.
        """
        return self.module_dirs | self.module_names | self._all_subdirs

    @cached_property
    def unique_owner(self) -> dict[str, str]:
        """realization name -> owning module, for names owned by exactly one.

        A shared name (`static`, `off`) cannot be attributed without a path.
        """
        owners: dict[str, set[str]] = {}
        for mod, reals in self.realizations_by_module.items():
            for r in reals:
                owners.setdefault(r, set()).add(mod)
        return {r: next(iter(m)) for r, m in owners.items() if len(m) == 1}

    def has_module(self, name: str) -> bool:
        return name in self.module_dirs

    def has_realization(self, name: str) -> bool:
        return name in self.realizations

    def is_realization_of(self, module_dir: str, name: str) -> bool:
        return name in self.realizations_by_module.get(module_dir, set())

    def default_of(self, module_dir: str) -> str | None:
        return self.defaults_by_module.get(module_dir)

    # ---- file-content facts (lazy) ---------------------------------------

    @cached_property
    def gms_paths(self) -> set[str]:
        out: set[str] = set()
        for base in ("modules", "core"):
            b = self.root / base
            if b.is_dir():
                out.update(str(p.relative_to(self.root)) for p in b.rglob("*.gms"))
        return out

    @cached_property
    def _content(self) -> tuple[set[str], set[str]]:
        """(identifiers, words) over every .gms file plus config/default.cfg."""
        idents: set[str] = set()
        words: set[str] = set()
        for rel in self.gms_paths:
            try:
                txt = (self.root / rel).read_text(errors="ignore")
            except OSError:
                continue
            idents.update(RE_GAMS_IDENT.findall(txt))
            words.update(re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", txt))
        # default.cfg names realizations and switches that appear nowhere in the
        # .gms tree (e.g. `cfg$gms$yields <- "managementcalib_aug19"`).
        if self._cfg_text:
            words.update(re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", self._cfg_text))
        return idents, words

    @property
    def identifiers(self) -> set[str]:
        return self._content[0]

    @property
    def words(self) -> set[str]:
        return self._content[1]

    def has_path(self, p: str) -> bool:
        return p in self.gms_paths

    def path_exists_under_some_realization(self, p: str) -> bool:
        """True if `modules/<mod>/<file>` exists as `modules/<mod>/<real>/<file>`.

        Distinguishes an omitted realization level (a citation defect -- the file
        is real) from a path that names nothing at all (a fabrication).
        """
        parts = p.split("/")
        if len(parts) != 3 or parts[0] != "modules":
            return False
        _, mod, fname = parts
        return any(
            q.startswith(f"modules/{mod}/") and q.endswith(f"/{fname}")
            for q in self.gms_paths
        )

    def path_exists_at_module_level(self, p: str) -> bool:
        """The mirror case: `modules/<mod>/<real>/<file>` cited when the file
        actually lives at `modules/<mod>/<file>` (`module.gms` is the usual one).
        Also a citation defect, not a fabrication."""
        parts = p.split("/")
        if len(parts) != 4 or parts[0] != "modules":
            return False
        _, mod, _real, fname = parts
        return f"modules/{mod}/{fname}" in self.gms_paths

    def line_count(self, p: str) -> int | None:
        """Number of lines in a tracked .gms file, or None if it is not one."""
        if p not in self.gms_paths:
            return None
        if p not in self._linecounts:
            try:
                self._linecounts[p] = len(
                    (self.root / p).read_text(errors="ignore").splitlines()
                )
            except OSError:
                self._linecounts[p] = 0
        return self._linecounts[p]

    def has_identifier(self, i: str) -> bool:
        return i in self.identifiers

    def is_identifier_prefix(self, i: str) -> bool:
        """True if `i` is a stem of a real identifier (`vm_peatland` for
        `vm_peatland_cost`). Answers use such stems as grep patterns; treating
        them as fabricated names is a false positive.

        NOT used by the citation checker -- see the module docstring.
        """
        return any(x.startswith(i + "_") for x in self.identifiers)

    def appears_anywhere(self, tok: str) -> bool:
        """True if the bare token occurs anywhere in the source or the config.

        Separates a genuinely invented name from a real thing mis-labelled as a
        realization: `kbe60` is a set, `yields` and `bioenergy` are module names,
        all present in the tree -- while `plant2forestry` occurs nowhere at all.
        """
        return tok in self.words or tok in self.module_names

    # ---- line-addressable reads (lazy, cached) ---------------------------

    def lines(self, rel: str) -> list[str] | None:
        if rel not in self._lines_cache:
            if not rel.startswith(ALLOWED_PREFIXES) or ".." in rel:
                self._lines_cache[rel] = None
            else:
                try:
                    self._lines_cache[rel] = (
                        (self.root / rel).read_text(errors="ignore").splitlines()
                    )
                except OSError:
                    self._lines_cache[rel] = None
        return self._lines_cache[rel]

    def equation_spans(self, rel: str) -> dict[str, tuple[int, int]]:
        """{equation name: (first line, terminator line)} for one file.

        A doc legitimately cites a BODY line of an equation while naming the
        equation for context -- `q30_prod` is defined at :14 but its body is :15.
        A proximity threshold cannot tell that apart from a citation that drifted
        onto a neighbouring equation; the span boundary can, categorically.
        Only equation names get this treatment: they are defined exactly once per
        file. Recurring symbols (vm_/pm_) have no unique anchor.
        """
        if rel in self._spans_cache:
            return self._spans_cache[rel]
        out: dict[str, tuple[int, int]] = {}
        lines = self.lines(rel) or []
        for i, ln in enumerate(lines, start=1):
            m = RE_EQN_DEF.match(ln)
            if not m:
                continue
            end = i
            for j in range(i, min(len(lines), i + 80)):
                end = j + 1
                if ";" in lines[j]:
                    break
            out[m.group(1)] = (i, end)
        self._spans_cache[rel] = out
        return out


# ==========================================================================
# Self-test for the SHARED layer itself
# ==========================================================================
#
# The point of these controls: after consolidation a defect here is CORRELATED
# across all three checkers. Testing this module only through its callers would
# mean a shared-layer bug is only ever visible as three simultaneous, separately
# confusing checker failures.

REGEX_POSITIVES = [
    ("RE_GAMS_IDENT matches an interface variable", RE_GAMS_IDENT, "vm_prod_reg", "vm_prod_reg"),
    ("RE_GAMS_IDENT matches a numbered local", RE_GAMS_IDENT, "s30_betr_target", "s30_betr_target"),
    ("RE_GAMS_IDENT matches an equation", RE_GAMS_IDENT, "q30_prod", "q30_prod"),
    ("RE_MODULE_DIR matches a module dir", RE_MODULE_DIR, "18_residues", "18_residues"),
    ("RE_GMS_PATH matches a modules path", RE_GMS_PATH,
     "modules/18_residues/flexreg_apr16/equations.gms", "modules/18_residues/flexreg_apr16/equations.gms"),
    ("RE_DATED_REALIZATION matches a dated name", RE_DATED_REALIZATION,
     "flexcluster_jul23", "flexcluster_jul23"),
]

REGEX_NEGATIVES = [
    ("RE_GAMS_IDENT does not match an unknown prefix", RE_GAMS_IDENT, "zz_notavariable"),
    ("RE_GAMS_IDENT does not match a bare word", RE_GAMS_IDENT, "production"),
    ("RE_DATED_REALIZATION does not match an undated name", RE_DATED_REALIZATION, "flexreg"),
]

# Guard controls. Each pairs a text that MUST trip the guard with one that must not.
GUARD_CASES = [
    ("negation: explicit non-existence phrase",
     is_negated, "There is no module 50_nsoil_budget in the tree.", "50_nsoil_budget", True),
    ("negation: bare cue in the left window",
     is_negated, "there is nothing here (no `s80_solprint` scalar).", "s80_solprint", True),
    ("negation: a plain assertion is NOT negated",
     is_negated, "The regional variable vm_prod_reg carries production.", "vm_prod_reg", False),
    # The cue must be NEAR. A negation 200 characters upstream is about something
    # else, and treating it as covering this token would silently delete real
    # findings -- the failure direction that does not announce itself.
    ("negation: a distant cue does not reach",
     is_negated,
     "There is no such thing as a free lunch. " + ("x" * 200) + " The variable vm_prod_reg exists.",
     "vm_prod_reg", False),
]


def _selftest_regexes() -> int:
    bad = 0
    print("== REGEX positive controls ==")
    for name, rx, text, expect in REGEX_POSITIVES:
        m = rx.search(text)
        got = m.group(1) if m else None
        ok = got == expect
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            bad += 1
            print(f"        expected {expect!r}, got {got!r}")
    print("== REGEX negative controls ==")
    for name, rx, text in REGEX_NEGATIVES:
        m = rx.search(text)
        ok = m is None
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            bad += 1
            print(f"        unexpected match: {m.group(0)!r}")
    return bad


CLAIM_NEGATION_CASES = [
    ("claim negation: explicit denial of the only token",
     "There is no such thing as `vm_fake` in this file.", ["vm_fake"], True),
    # The case that caught the first, too-blunt implementation. An unrelated
    # "not" elsewhere in the clause must NOT read as denying the identifier.
    ("claim negation: an unrelated 'not' does not deny the token",
     "`vm_fake` is not optional and is defined here.", ["vm_fake"], False),
    ("claim negation: one token asserted positively defeats the guard",
     "There is no `vm_fake`, but `vm_prod_reg` is defined here.",
     ["vm_fake", "vm_prod_reg"], False),
    ("claim negation: no tokens is not a denial", "nothing here", [], False),
    # The 36-character "not" that suppressed a citation finding for the wrong
    # reason (2026-08-01 consolidation diff).
    ("claim negation: a cue 30+ chars away does not deny",
     "not solved for) every timestep in `vm_prod_reg`", ["vm_prod_reg"], False),
]


def _selftest_guards() -> int:
    bad = 0
    print("== GUARD controls ==")
    for name, fn, text, token, expect in GUARD_CASES:
        i = text.find(token)
        got = fn(text, (i, i + len(token)))
        ok = got is expect
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  (expect {expect})")
        if not ok:
            bad += 1
    for name, clause, tokens, expect in CLAIM_NEGATION_CASES:
        got = is_negated_claim(clause, tokens)
        ok = got is expect
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  (expect {expect})")
        if not ok:
            bad += 1
    for name, tok, expect in [
        ("glob stem: trailing underscore is a stem", "vm_dem_", True),
        ("glob stem: a real identifier is not", "vm_dem_food", False),
        ("elided path is elided", "modules/40_transport/.../equations.gms", True),
        ("filename: a .gms basename names a location", "presolve.gms", True),
        ("filename: an identifier is not a filename", "vm_prod_reg", False),
    ]:
        fn = (is_elided_path if "/" in tok
              else is_filename if "." in tok
              else is_glob_stem)
        got = fn(tok)
        ok = got is expect
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            bad += 1
    return bad


def _selftest_tree(tree: Tree) -> int:
    """Structural invariants of the oracle, checked against the real tree."""
    bad = 0
    print("== TREE controls ==")
    checks = [
        ("every module resolves a default", len(tree.defaults_by_module) == len(tree.module_dirs),
         f"{len(tree.defaults_by_module)}/{len(tree.module_dirs)}"),
        ("every default names a real realization",
         all(tree.is_realization_of(m, d) for m, d in tree.defaults_by_module.items()), ""),
        ("`input` is NOT a realization", "input" not in tree.realizations, ""),
        ("`input` IS a directory name", "input" in tree.dir_names, ""),
        ("realizations are a subset of dir_names", tree.realizations <= tree.dir_names, ""),
        ("module 80's default is a substring of a non-default (boundary hazard is live)",
         "nlp_apr17" in tree.realizations_by_module.get("80_optimization", set())
         and "lp_nlp_apr17" in tree.realizations_by_module.get("80_optimization", set()), ""),
        ("module 73 has a realization literally named `default`",
         "default" in tree.realizations_by_module.get("73_timber", set()), ""),
    ]
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}{('  ' + detail) if detail else ''}")
        if not ok:
            bad += 1
    return bad


def selftest(tree: Tree) -> int:
    bad = _selftest_regexes() + _selftest_guards() + _selftest_tree(tree)
    print(f"\nshared-layer self-test: {bad} failure(s)")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    tree = Tree(Path(a.root).resolve())
    print(
        f"tree: {len(tree.module_dirs)} modules, {len(tree.realizations)} realizations, "
        f"{len(tree.defaults_by_module)} defaults",
        file=sys.stderr,
    )
    if not a.selftest:
        ap.error("this module is a library; run with --selftest")
    return 1 if selftest(tree) else 0


if __name__ == "__main__":
    raise SystemExit(main())
