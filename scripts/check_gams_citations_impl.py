#!/usr/bin/env python3
"""Verify file:line citations in AI docs against GAMS code.

Checks:
  1. file.gms:NN references point to files that exist with >= NN lines
  2. Range citations file.gms:NN-MM verify both NN and MM
  3. Bare-basename citations (no realization path) WARN when the basename
     matches multiple realizations under the same module — silently picking
     the first is the MANDATE 16 / R1 Cluster 2 hazard
  4. When a backticked GAMS identifier (vm_*/pm_*/v<N>_*/p<N>_*/s<N>_*/
     c<N>_*/q<N>_*) appears within ~80 chars of a citation, verify the
     identifier appears at or near the cited line (within +/-5 lines).
     Pattern 12 (Content-Level Citation Mismatch) — R1 Cluster 2.
  5. Adjacent-line drift pre-flag: a single-line cite of an equation NAME
     (qNN_*, defined exactly once per equations.gms) whose definition lands
     within +/-5 of the cited line but >=2 lines off it; i.e. the cite drifted
     onto a similar-content NEIGHBOR block. Equation names disambiguate which
     block is meant (vm_/pm_/scalars recur, so are excluded). Advisory.
     Closes the "too tolerant of similar-content neighbors" gap (BACKLOG R25).

Reports:
  FILE: missing file
  LINE: out-of-range line (start or end of range)
  AMBIG: bare-basename with multiple-realization ambiguity (WARN)
  CONTENT: identifier not found near cited line (WARN, content mismatch)
  STRICT: declarations.gms/input.gms identifier not at the EXACT cited line (WARN)
  DRIFT: single-line equation-name cite drifted within the +/-5 window (WARN)
"""

import subprocess, re, os, sys, shutil, tempfile, textwrap
from collections import defaultdict


# Match a citation followed by an OPTIONAL range end and OPTIONAL comma-list
# continuation (the pervasive discontiguous multi-line cite format):
#   `file.gms:50`            → start=50, end=None,  cont=None
#   `file.gms:50-75`         → start=50, end=75,    cont=None
#   `file.gms:25,24,26`      → start=25, end=None,  cont=",24,26"   (3 single lines)
#   `file.gms:14-16, 21-29`  → start=14, end=16,    cont=", 21-29"  (range + a range)
#   `file.gms:66, 77, 131`   → start=66, end=None,  cont=", 77, 131" (3 single lines)
# An OPTIONAL single space after each comma is allowed: both `:N,M` and `:N, M`
# occur in the corpus (~100 no-space + ~64 spaced). A DIGIT must follow the comma,
# so prose like "file.gms:50, and ..." does NOT match (the first cite stands
# alone). The only residual ambiguity ("file.gms:50, 9000 widgets") does not
# occur in this corpus (all 64 spaced matches verified to be line-lists 2026-06-05).
CITATION_RE = re.compile(r'((?:core/|modules/[\w/]+/)?[\w/]+\.gms):(\d+)(?:-(\d+))?((?:, ?\d+(?:-\d+)?)+)?')

# GAMS identifier classes (used by Pattern 12 content check)
GAMS_ID_RE = re.compile(r'`((?:vm|pm|v|p|i|f|s|c|cm|sm|im|fm|pcm|ic|ov|oq|q)\d*_[a-zA-Z][\w]*)`')

# Equation-name subclass (qNN_*). An equation is DEFINED exactly once per
# equations.gms (the `qNN_name(dom) ..` line), so its definition line is an
# unambiguous citation anchor, used by the adjacent-line drift pre-flag (Check 5).
# vm_/pm_/scalars recur across every using-equation and are deliberately NOT in
# this class (their "nearest occurrence" is ambiguous, so drift can't be inferred).
EQ_NAME_RE = re.compile(r'q\d+_')


def eq_span_end(lines, def_line, total_lines, max_scan=40):
    """Line number of the `;` terminating the equation that starts at def_line.

    Scans at most max_scan lines forward from def_line (1-based) for the
    statement terminator. GAMS equations always end in `;`, so the fallback
    (def_line + max_scan, clamped) only matters for malformed/truncated input.
    Used by both the DRIFT pre-flag (Check 5) and the CONTENT check's
    equation-body-cite guard to tell a legitimate body-line citation (cited line
    INSIDE the named equation's [def..terminator] span) from a real drift.
    """
    end = def_line
    for i in range(def_line, min(total_lines, def_line + max_scan) + 1):
        end = i
        if i - 1 < len(lines) and lines[i - 1].rstrip().endswith(';'):
            break
    return end

# Contrastive-phrase patterns: when a backticked identifier is preceded by
# language like "instead of", "not", "differs from", "unlike", "rather than",
# or "vs", the identifier is being mentioned as a CONTRAST (what the cited
# content is NOT) rather than as the subject of the cite. Suppress pairings
# where the identifier is preceded by one of these phrases within ~30 chars.
# R25 follow-up: caught vm_tau-in-module_14, s32_aff_plantation-in-module_52,
# s80_obj_linear-in-module_80.
CONTRASTIVE_PHRASE_RE = re.compile(
    r"\b(?:instead of|rather than|not(?:\s+from)?|differs? from|unlike|"
    r"compared (?:to|with)|vs\.?|versus|opposite of|in contrast(?:\s+to)?|"
    r"as opposed to|whereas|while)\s*$",
    re.IGNORECASE,
)

# Subject-boundary pattern: text like `) and `, `) or `, `) while `, `; and `
# between an identifier and a citation signals that the identifier was in a
# PRIOR clause and the citation belongs to a DIFFERENT subject. Used to
# suppress pairings across clause boundaries on the same line. R25 follow-up:
# caught s32_aff_plantation-in-module_52 multi-cite line.
SUBJECT_BOUNDARY_RE = re.compile(
    r"\)\s*(?:and|or|while|whereas|but)\s+",
    re.IGNORECASE,
)

# Path-based exclusions: certain docs are PEDAGOGICAL — they cite identifiers
# that intentionally illustrate bug patterns, drift cases, or hypothetical
# scenarios. Suppressing them from the content check avoids chronic FPs.
# Bug_Taxonomy.md is the canonical example (it teaches what doc bugs LOOK
# like by showing intentionally-broken cites).
PEDAGOGICAL_DOCS = {"Bug_Taxonomy.md"}

# Scaffolding files: realization.gms is typically just $include directives
# pulling in declarations.gms / equations.gms / etc. — it rarely contains
# variable or equation definitions. Citations pointing at realization.gms
# usually reference the module's CONFIGURATION not its variable definitions,
# so identifier-content checks generate FPs.
SCAFFOLDING_BASENAMES = {"realization.gms", "module.gms"}

# Structured-section labels used for cross-line lookback (R25 Phase 1 follow-up).
# When a doc presents:
#     **Variable:** `vm_foo`
#     ...
#     **Citation:** `file.gms:NN`
# the identifier and citation are on different lines, so the per-line nearby_ids
# window misses the pairing. Look back up to 5 non-empty lines for one of these
# labels and add any backticked identifier on that label-line to nearby_ids.
STRUCT_LABEL_RE = re.compile(
    r"\*\*(?:Variable|Equation|Source|Source Module|Output|Interface|Provides)[: ]"
)
# Lines that mark a HARD STOP for cross-line lookback — they signal we've
# entered a different documentation block whose identifier shouldn't be paired
# with the current citation. The check is on prefix because we want to match
# the entire `**File:**` / `**Citation:**` field-label including the colon.
BOUNDARY_RE = re.compile(
    r"^\s*(?:#{2,6}\s|\*\*(?:File|Citation|Location|Defined in)[: ])"
)


def self_test():
    """Positive-control self-test for Check 17 (file:line citation checker).

    Builds a self-contained temp fixture (never touches the real modules/ tree)
    that exercises the three outcomes the checker must distinguish:

      A. Full-path cite to the SHORT realization (off/, 18 lines) at line 80
         → must FLAG as LINE error.  Proves the checker catches out-of-range cites.

      B. Bare-basename cite `declarations.gms:80` that resolves via
         config/default.cfg to the DEFAULT realization (v2/, 85 lines)
         → must PASS.  This is the exact f4f44b0 behaviour: bare cites go to
         the default realization, not to whatever walk-order returns first.
         Regression of this fix would cause every bare cite past line 18 to
         be a false LINE error (the original f4f44b0 symptom).

      C. Full-path cite to the LONG realization (v2/, 85 lines) at line 80
         → must PASS (clean control: valid in-range citation).

    The test re-invokes this script as a subprocess so it exercises the
    complete pipeline (file-index build, config parse, rg scan, resolution
    logic, line-count check) on the fixture without touching any real files.
    """
    ok = True
    tmpdir = tempfile.mkdtemp(prefix='check17_selftest_')
    try:
        # ── Build fixture ────────────────────────────────────────────────────
        magpie_root = os.path.join(tmpdir, 'magpie')
        agent_dir   = os.path.join(tmpdir, 'agent')

        # GAMS tree: two realizations of module 58
        off_dir = os.path.join(magpie_root, 'modules', '58_peatland', 'off')
        v2_dir  = os.path.join(magpie_root, 'modules', '58_peatland', 'v2')
        os.makedirs(off_dir)
        os.makedirs(v2_dir)
        os.makedirs(os.path.join(magpie_root, 'config'))
        os.makedirs(os.path.join(agent_dir, 'modules'))

        # off/declarations.gms — 18 lines (short realization)
        with open(os.path.join(off_dir, 'declarations.gms'), 'w') as f:
            for i in range(1, 19):
                f.write(f'* line {i}\n')

        # v2/declarations.gms: 85 lines (default realization). Lines 24/25/26
        # carry real one-per-line var declarations (v58_alpha/beta/gamma) for the
        # comma-list STRICT sibling-guard test (assertion F); the v30_betr_missing
        # FP geometry: three vars named together, each on its own listed line.
        with open(os.path.join(v2_dir, 'declarations.gms'), 'w') as f:
            for i in range(1, 86):
                if i == 24:
                    f.write(' v58_alpha(j)   alpha var (mio. ha)\n')
                elif i == 25:
                    f.write(' v58_beta(j)    beta var (mio. ha)\n')
                elif i == 26:
                    f.write(' v58_gamma(j)   gamma var (mio. ha)\n')
                else:
                    f.write(f'* line {i}\n')

        # v2/equations.gms: two equations on KNOWN lines, for the adjacent-line
        # drift pre-flag (assertion D). q58_foo is DEFINED at line 4, q58_bar at
        # line 9, a stack of similar `q58_*(i2) ..` blocks that mirrors module_53's
        # four near-identical q53_emissionbal_ch4_* equations (the real "similar-
        # content neighbor" geometry the +/-5 fingerprint window is too loose for).
        eqlines = [
            "*' equation header",             # 1
            "*' explanatory comment",         # 2
            "",                                # 3
            " q58_foo(i2) ..",                # 4  <- q58_foo DEFINITION
            '   vm_a(i2,"x") =e= pm_b(i2);',  # 5
            "",                                # 6
            "*' comment about the bar flow",  # 7
            "",                                # 8
            " q58_bar(i2) ..",                # 9  <- q58_bar DEFINITION
            '   vm_c(i2,"y") =e= pm_d(i2);',  # 10
            "",                                # 11
            "*' trailing filler",             # 12
            "*' trailing filler",             # 13
            "*' trailing filler",             # 14
            "",                                # 15
            " q58_long(i2) ..",               # 16 <- q58_long DEFINITION (long eq)
            "   vm_e(i2) =e= vm_f(i2)",       # 17
            "     + vm_g(i2)",                # 18
            "     + vm_h(i2)",                # 19
            "     + vm_i(i2)",                # 20
            "     + vm_j(i2)",                # 21
            "     + vm_k(i2)",                # 22
            "     + vm_l(i2)",                # 23
            "     + vm_m(i2)",                # 24 <- body line, 8 lines from def 16
            "     + vm_n(i2);",               # 25 <- q58_long TERMINATOR (`;`)
            "",                                # 26
            "*' filler after the long eq",    # 27
            "*' filler after the long eq",    # 28
        ]
        with open(os.path.join(v2_dir, 'equations.gms'), 'w') as f:
            f.write("\n".join(eqlines) + "\n")

        # config/default.cfg — sets peatland default to v2
        with open(os.path.join(magpie_root, 'config', 'default.cfg'), 'w') as f:
            f.write('cfg$gms$peatland <- "v2"\n')

        # AI doc with three citations:
        #   (A) full path to off/ at line 80  → out of range (off has 18 lines)
        #   (B) bare basename at line 80       → resolved to v2/ (85 lines) → in range
        #   (C) full path to v2/ at line 80   → in range (v2 has 85 lines)
        doc = textwrap.dedent("""\
            # Test doc

            Citation A (full path, out-of-range realization): modules/58_peatland/off/declarations.gms:80

            Citation B (bare basename, must resolve to default v2): declarations.gms:80

            Citation C (full path, in-range realization): modules/58_peatland/v2/declarations.gms:80

            Citation D (adjacent-line drift): the `q58_foo` balance at modules/58_peatland/v2/equations.gms:7

            Citation E (clean control): the `q58_bar` balance at modules/58_peatland/v2/equations.gms:9

            Citation F (in-equation body cite, >5 from def): the `q58_long` aggregate at modules/58_peatland/v2/equations.gms:24

            Citation G (out-of-equation cite, must still flag): the `q58_long` aggregate at modules/58_peatland/v2/equations.gms:28

            Comma-list STRICT fixture (vars at sibling lines; table row for full-window id capture):

            | `v58_alpha` | `v58_beta` | `v58_gamma` | modules/58_peatland/v2/declarations.gms:24,25,26 |

            Citation I (comma-list out-of-range continuation, no space): modules/58_peatland/off/declarations.gms:5,200

            Citation J (comma-list out-of-range continuation, WITH space): modules/58_peatland/off/declarations.gms:6, 250
        """)
        with open(os.path.join(agent_dir, 'modules', 'module_58.md'), 'w') as f:
            f.write(doc)

        # ── Run checker on fixture ───────────────────────────────────────────
        result = subprocess.run(
            [sys.executable, __file__, agent_dir, magpie_root],
            capture_output=True, text=True
        )
        stdout = result.stdout + result.stderr

        # ── Assertion A: checker must FLAG the off/ out-of-range cite ────────
        # exit code 1 means at least one LINE/FILE error was found
        if result.returncode != 1:
            print(f"  SELF-TEST FAIL [A]: expected exit code 1 (out-of-range cite "
                  f"in off/ not caught), got {result.returncode}")
            print(f"  Output was:\n{stdout}")
            ok = False
        # The error detail must mention the off/ path and line 80
        if 'off/declarations.gms:80' not in stdout and 'off\\declarations.gms:80' not in stdout:
            print("  SELF-TEST FAIL [A]: LINE error for off/declarations.gms:80 "
                  "not found in output")
            print(f"  Output was:\n{stdout}")
            ok = False

        # ── Assertion B: bare cite at line 80 must NOT produce a LINE error ──
        # The bare cite `declarations.gms:80` must resolve to v2/ (85 lines).
        # If the f4f44b0 bare-cite resolution regressed (e.g. walk-order returns
        # off/ first), line 80 would exceed off/'s 18 lines and appear here as
        # a second LINE error — the test would then see two LINE errors instead
        # of one, proving the regression.
        line_errors = [ln for ln in stdout.splitlines()
                       if ln.lstrip().startswith('LINE:')]
        # Exactly one LINE error expected (the off/ cite in assertion A)
        off_errors = [ln for ln in line_errors
                      if 'off' in ln or 'off\\' in ln]
        bare_or_v2_errors = [ln for ln in line_errors
                             if 'off' not in ln and 'off\\' not in ln]
        if bare_or_v2_errors:
            print("  SELF-TEST FAIL [B]: bare or v2 citation at line 80 was "
                  "incorrectly flagged as LINE error — bare-cite resolution "
                  "likely regressed to walk-order (returning off/ instead of v2/)")
            for e in bare_or_v2_errors:
                print(f"    {e}")
            ok = False

        # ── Assertion C: v2/ full-path cite at line 80 must pass ─────────────
        # (This is subsumed by assertion B's check above, but stated explicitly
        # for documentation clarity — if C fired it would appear in bare_or_v2_errors)
        v2_errors = [ln for ln in line_errors if 'v2' in ln]
        if v2_errors:
            print("  SELF-TEST FAIL [C]: full-path v2/declarations.gms:80 was "
                  "flagged as out-of-range (v2 has 85 lines — should be in range)")
            ok = False

        # ── Assertion D: equation-name adjacent-line drift must be pre-flagged ─
        # q58_foo is DEFINED at line 4 but cited single-line at :7 (delta -3,
        # INSIDE the +/-5 fingerprint window). The fingerprint check alone passes
        # it (q58_foo IS within +/-5 of line 7); the new equation-name drift
        # pre-flag (Check 5) must catch it and point at the real definition line.
        drift_lines = [ln for ln in stdout.splitlines()
                       if ln.lstrip().startswith('DRIFT:')]
        if not any('q58_foo' in ln and '~:4' in ln for ln in drift_lines):
            print("  SELF-TEST FAIL [D]: q58_foo cited at :7 but defined at line 4 "
                  "(adjacent-line drift inside the +/-5 window) was NOT pre-flagged "
                  "as DRIFT; fingerprint tightening regressed")
            print(f"  Output was:\n{stdout}")
            ok = False
        # Clean control: q58_bar cited at its OWN definition line (9) must NOT flag.
        bar_fp = [ln for ln in drift_lines if 'q58_bar' in ln]
        if bar_fp:
            print("  SELF-TEST FAIL [D]: q58_bar cited at its definition line was "
                  "incorrectly flagged as DRIFT (false positive)")
            for e in bar_fp:
                print(f"    {e}")
            ok = False

        # ── Assertion E: CONTENT equation-body-cite guard ────────────────────
        # q58_long is DEFINED at line 16 and spans 16..25. Citation F cites a BODY
        # line (:24, 8 lines from the def, beyond the +/-5 fingerprint), so the
        # CONTENT guard must SUPPRESS it (legitimate in-equation provenance cite,
        # the module_54.md `q11_cost_reg`:25 pattern). Citation G cites OUTSIDE the
        # equation (:28), so CONTENT must STILL fire. Net: exactly ONE CONTENT
        # warning should mention q58_long.
        #   0 -> guard over-suppressed a genuine far-cite (Citation G missed)
        #   2 -> guard failed to suppress the legitimate body cite (Citation F FP)
        long_content = [ln for ln in stdout.splitlines()
                        if ln.lstrip().startswith('CONTENT:') and 'q58_long' in ln]
        if len(long_content) == 0:
            print("  SELF-TEST FAIL [E]: CONTENT guard OVER-suppressed; the "
                  "out-of-equation cite q58_long:28 should still be flagged as CONTENT")
            print(f"  Output was:\n{stdout}")
            ok = False
        elif len(long_content) >= 2:
            print("  SELF-TEST FAIL [E]: CONTENT guard did NOT suppress the "
                  "legitimate in-equation body cite q58_long:24 (defined :16, spans "
                  ":16-25); equation body-line provenance cites would false-positive")
            for e in long_content:
                print(f"    {e}")
            ok = False

        # ── Assertion F: comma-list multi-cite STRICT sibling guard ───────────
        # The table-row cite names v58_alpha/beta/gamma at declarations.gms:24,25,26;
        # those vars live at lines 24/25/26 respectively. Each is at ONE listed
        # line, so STRICT must NOT flag any (the v30_betr_missing FP class). Teeth:
        # without comma-list parsing + the sibling guard, beta@25 and gamma@26
        # (not at the parsed primary :24) would each be flagged STRICT.
        strict_warns = [ln for ln in stdout.splitlines()
                        if ln.lstrip().startswith('STRICT:')
                        and ('v58_alpha' in ln or 'v58_beta' in ln or 'v58_gamma' in ln)]
        if strict_warns:
            print("  SELF-TEST FAIL [F]: comma-list cite :24,25,26 naming three vars "
                  "at those exact lines was flagged STRICT; the sibling-line guard or "
                  "comma-list parsing regressed")
            for e in strict_warns:
                print(f"    {e}")
            ok = False

        # ── Assertion G: comma-list continuation existence-checking ───────────
        # Citation I (`:5,200`, no space) and J (`:6, 250`, WITH space) both cite
        # off/declarations.gms (18 lines), so the :200 and :250 CONTINUATIONS are
        # out of range and must each be flagged as a LINE error. Covers both
        # comma-list spellings. Teeth: if continuations were dropped (old
        # behavior), they are never parsed, never checked, and no error appears.
        for bad in ('200', '250'):
            spelling = 'no-space (:5,200)' if bad == '200' else 'spaced (:6, 250)'
            if (f'off/declarations.gms:{bad}' not in stdout
                    and f'off\\declarations.gms:{bad}' not in stdout):
                print(f"  SELF-TEST FAIL [G]: out-of-range comma-list continuation "
                      f"off/declarations.gms:{bad} ({spelling}, file has 18 lines) was "
                      f"NOT flagged; comma-list continuations not existence-checked")
                print(f"  Output was:\n{stdout}")
                ok = False

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if ok:
        print("SELF-TEST PASS: Check 17 (file:line citations)")
        print("  [A] Out-of-range cite in off/ (18 lines) correctly flagged as LINE error")
        print("  [B] Bare-basename cite at line 80 correctly resolves to default v2/ "
              "(85 lines) and passes — f4f44b0 bare-cite resolution intact")
        print("  [C] Full-path cite to v2/ at line 80 correctly passes")
        print("  [D] Single-line equation-name cite drifted onto a neighbor block "
              "(q58_foo cited :7, defined :4) correctly pre-flagged as DRIFT; clean "
              "control (q58_bar at its def line) correctly not flagged")
        print("  [E] CONTENT equation-body-cite guard: in-equation body cite "
              "(q58_long :24, spans :16-25) correctly suppressed; out-of-equation "
              "cite (q58_long :28) correctly still flagged")
        print("  [F] Comma-list STRICT sibling guard: :24,25,26 naming three vars at "
              "those exact lines correctly NOT flagged (v30_betr_missing FP class)")
        print("  [G] Comma-list continuation existence-checked: out-of-range :200 in "
              "a `:5,200` cite correctly flagged as LINE error")
        return 0
    else:
        print("SELF-TEST FAIL: one or more assertions failed (see above)")
        return 1


def main():
    if '--self-test' in sys.argv:
        rc = self_test()
        if rc == 0:
            print("SELFTEST_OK check_gams_citations_impl")
        sys.exit(rc)

    agent_dir = sys.argv[1]
    magpie_root = sys.argv[2]

    # Build file index: basename -> [full_paths]
    file_index = defaultdict(list)
    for root, dirs, files in os.walk(os.path.join(magpie_root, 'modules')):
        for f in files:
            if f.endswith('.gms'):
                file_index[f].append(os.path.join(root, f))
    for root, dirs, files in os.walk(os.path.join(magpie_root, 'core')):
        for f in files:
            if f.endswith('.gms'):
                file_index[f].append(os.path.join(root, f))

    # Map module number -> DEFAULT realization dir (from config/default.cfg).
    # A bare-basename cite (`declarations.gms:NN` with no realization path) must
    # resolve to the realization MAgPIE compiles by DEFAULT, not whatever the
    # filesystem walk returns first. Walk-order resolution measured cites against
    # the wrong (often shorter) realization and produced false LINE errors — e.g.
    # module_58.md cites resolved to 58_peatland/off/ (18 lines) instead of the
    # default v2/ (85 lines), flagging every cite past line 18.
    modules_dir = os.path.join(magpie_root, 'modules')
    suffix_to_num = {}
    if os.path.isdir(modules_dir):
        for d in os.listdir(modules_dir):
            md = re.match(r'^(\d+)_(.+)$', d)
            if md and os.path.isdir(os.path.join(modules_dir, d)):
                suffix_to_num[md.group(2)] = md.group(1)
    module_default_realization = {}
    cfg_re = re.compile(r'cfg\$gms\$(\w+)\s*<-\s*"([^"]+)"')
    try:
        with open(os.path.join(magpie_root, 'config', 'default.cfg'),
                  'r', errors='replace') as cfgf:
            for cfg_line in cfgf:
                cm = cfg_re.search(cfg_line)
                if not cm:
                    continue
                key, real = cm.group(1), cm.group(2).strip()
                # Skip composite/multi-token defaults (e.g. "a, b, c") — no
                # single realization dir; fall through to walk-order for those.
                if ',' in real or ' ' in real:
                    continue
                num = suffix_to_num.get(key)
                # Only trust the mapping if the realization dir actually exists.
                if num and os.path.isdir(os.path.join(modules_dir, f'{num}_{key}', real)):
                    module_default_realization[num] = real
    except OSError:
        pass

    # Cache file contents (only when needed)
    file_lines_cache = {}

    def get_lines(path):
        if path not in file_lines_cache:
            try:
                with open(path, 'r', errors='replace') as f:
                    file_lines_cache[path] = f.read().splitlines()
            except (OSError, UnicodeDecodeError):
                file_lines_cache[path] = []
        return file_lines_cache[path]

    # Cache of DOC file lines (needed for cross-line lookback of structured sections).
    # Distinct from file_lines_cache (which caches GAMS source files).
    doc_lines_cache = {}

    def get_doc_lines(path):
        if path not in doc_lines_cache:
            try:
                with open(path, 'r', errors='replace') as f:
                    doc_lines_cache[path] = f.read().splitlines()
            except (OSError, UnicodeDecodeError):
                doc_lines_cache[path] = []
        return doc_lines_cache[path]

    # Extract citations + nearby context from AI docs.
    # R5 (2026-05-24): scope extended from modules/-only to all doc directories
    # to close the Pattern 10 FN gap (151 historical bugs were file:line drift,
    # 80% in non-module docs that were previously unchecked).
    scan_paths = [
        os.path.join(agent_dir, 'modules/'),
        os.path.join(agent_dir, 'cross_module/'),
        os.path.join(agent_dir, 'core_docs/'),
        os.path.join(agent_dir, 'agent/helpers/'),
        os.path.join(agent_dir, 'agent/commands/'),
        os.path.join(agent_dir, 'reference/'),
        os.path.join(agent_dir, 'AGENT.md'),
        os.path.join(agent_dir, 'README.md'),
    ]
    scan_paths = [p for p in scan_paths if os.path.exists(p)]
    if shutil.which('rg') is None:
        print("ERROR: ripgrep (rg) is required by check_gams_citations_impl but was not "
              "found on PATH. Install it (apt-get install ripgrep / brew install ripgrep).",
              file=sys.stderr)
        sys.exit(2)
    result = subprocess.run(
        ['rg', '-n', r'\w+\.gms:\d+'] + scan_paths,
        capture_output=True, text=True
    )

    citations = {}  # (doc_file, mod_num, gms_hint, start, end) -> {nearby_ids}
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        # Match any .md file. If filename is `module_NN.md` (with optional
        # _notes.md / _other.md suffix), capture NN as mod_num for bare-
        # basename rescue. Otherwise mod_num is None: bare-basename
        # citations in non-module docs must use full paths per MANDATE 16.
        m = re.match(r'^(.+\.md):(\d+):(.+)', line)
        if not m:
            continue
        doc_file, doc_line_str, context = m.group(1), m.group(2), m.group(3)
        doc_line_idx = int(doc_line_str) - 1
        mod_match = re.search(r'/module_(\d+)\w*\.md$', doc_file)
        mod_num = mod_match.group(1) if mod_match else None

        # Detect table-row context: lines starting with `|` are markdown table
        # rows. In tables, citations and their subject identifier are typically
        # in different cells separated by ~50-150 chars. The 40-char back
        # window misses these. Drop the per-char limit on table rows; rely
        # only on the previous-cite cut-off to avoid sibling-cell collisions.
        is_table_row = context.lstrip().startswith("|")

        # Find all citations on this line so we can scope each nearby_ids window
        # only to the text between this cite and the previous one (avoids picking
        # up identifiers that belong to a sibling citation in the same prose).
        cite_matches = list(CITATION_RE.finditer(context))
        for idx, cit_match in enumerate(cite_matches):
            gms_hint = cit_match.group(1)
            start = int(cit_match.group(2))
            end = int(cit_match.group(3)) if cit_match.group(3) else None
            # Comma-list continuation, e.g. `equations.gms:25,24,26` or `:20,27-28`.
            # Each `,N` or `,N-M` is an ADDITIONAL cited line/range for the SAME
            # concept. Parse them so every listed line gets existence-checked and
            # so the content/strict checks accept an identifier found at ANY listed
            # line (else a doc naming three vars at :25,24,26 false-positives on the
            # parsed primary :25). Stored as a hashable tuple for the citation key.
            extra = ()
            if cit_match.group(4):
                pairs = []
                for tok in cit_match.group(4).split(',')[1:]:
                    tok = tok.strip()  # may carry a leading space from `:N, M`
                    if '-' in tok:
                        a, b = tok.split('-', 1)
                        pairs.append((int(a), int(b)))
                    else:
                        pairs.append((int(tok), None))
                extra = tuple(pairs)

            # Capture nearby backticked GAMS identifiers. For PROSE: tighter
            # window — back to previous cite (or 40 chars, whichever is closer)
            # plus 10 chars forward (cites typically follow their subject).
            # For TABLE ROWS: no per-char back limit (cells can be long); only
            # the previous-cite bound applies.
            prev_end = cite_matches[idx - 1].end() if idx > 0 else 0
            if is_table_row:
                window_start = prev_end
            else:
                window_start = max(prev_end, cit_match.start() - 40)
            window_end = min(len(context), cit_match.end() + 10)
            window = context[window_start:window_end]
            # The cite's offset within the window (used by the subject-boundary
            # check to know what's "between identifier and cite")
            cite_offset_in_window = cit_match.start() - window_start
            # Extract all identifier matches with positions so we can apply
            # the contrastive-phrase and subject-boundary filters per match.
            id_matches = list(GAMS_ID_RE.finditer(window))
            nearby_ids = set()
            for im in id_matches:
                # CONTRASTIVE PHRASE: look at the 30 chars immediately preceding
                # this identifier within the window. Skip if a contrastive
                # phrase ends right before the identifier.
                preceding = window[max(0, im.start() - 30):im.start()]
                if CONTRASTIVE_PHRASE_RE.search(preceding):
                    continue
                # SUBJECT BOUNDARY: if the text between this identifier's end
                # and the cite's start contains a clause-boundary pattern
                # (`) and `, `) or `, etc.), the identifier was in a different
                # clause. Skip.
                if im.end() < cite_offset_in_window:
                    between = window[im.end():cite_offset_in_window]
                    if SUBJECT_BOUNDARY_RE.search(between):
                        continue
                nearby_ids.add(im.group(1))

            # CROSS-LINE LOOKBACK (R25 Phase 1 follow-up):
            # If no identifier found in the same-line window, look back up to
            # 5 non-empty lines for a structured-section label (**Variable:**,
            # **Equation:**, etc.) with a backticked identifier. This catches
            # the `**Variable:** \`vm_X\`` ... `**Citation:** \`file:NN\`` pattern
            # used pervasively in module_11.md cost-component sections.
            #
            # HARD STOP at section boundaries (markdown headers #### / ###,
            # or another **File:** / **Citation:** / **Location:** label).
            # Without this, lookback crosses block boundaries and pairs the
            # PREVIOUS block's identifier with this block's citation — false
            # positive observed in module_14.md per-forest-type sections.
            if not nearby_ids:
                doc_lines = get_doc_lines(doc_file)
                lookback_count = 0
                for j in range(doc_line_idx - 1, max(-1, doc_line_idx - 12), -1):
                    if j < 0 or j >= len(doc_lines):
                        break
                    prev_line = doc_lines[j]
                    if not prev_line.strip():
                        continue  # skip blank lines, don't count toward limit
                    if BOUNDARY_RE.search(prev_line):
                        break  # crossed a section boundary; don't reach further
                    lookback_count += 1
                    if lookback_count > 5:
                        break
                    if STRUCT_LABEL_RE.search(prev_line):
                        found = set(GAMS_ID_RE.findall(prev_line))
                        if found:
                            nearby_ids.update(found)
                            break

            key = (doc_file, mod_num, gms_hint, start, end, extra)
            if key not in citations:
                citations[key] = nearby_ids
            else:
                citations[key].update(nearby_ids)

    valid = 0
    file_missing = 0
    line_over = 0
    ambig = 0
    content_miss = 0
    details = []
    warnings = []

    def sort_key(item):
        (doc_file, mod_num, gms_hint, start, end, _extra), _ = item
        return (doc_file, mod_num, gms_hint, start, end if end is not None else -1)

    for (doc_file, mod_num, gms_hint, start, end, extra), nearby_ids in sorted(citations.items(), key=sort_key):
        actual = None
        basename = os.path.basename(gms_hint)
        doc_short = os.path.basename(doc_file)
        # Every cited (start, end) range for this citation: the primary plus any
        # comma-list continuations. Drives existence-checking of every listed line
        # and lets the content/strict checks accept an identifier at ANY listed line.
        line_ranges = [(start, end)] + list(extra)

        # Full-path citation — best case. If the doc cited a full path
        # (modules/... or core/...) and that file doesn't exist, the path
        # is wrong. Do NOT fall through to bare-basename rescue: that would
        # silently launder a fabricated realization into a real file and
        # defeat MANDATE 16. Report FILE missing immediately.
        # Note: in non-module docs (mod_num=None), surface as advisory —
        # these docs often contain pedagogical format examples (e.g.,
        # README.md's "Mandatory Citation Format" section, AGENT.md's
        # epistemic-hierarchy templates with NN_xxx placeholders).
        if gms_hint.startswith('core/') or gms_hint.startswith('modules/'):
            full = os.path.join(magpie_root, gms_hint)
            if os.path.isfile(full):
                actual = full
            else:
                if mod_num is None:
                    ambig += 1
                    warnings.append(
                        f"  FILE-NM: {gms_hint}:{start} (in {doc_short}) — full path "
                        f"does not exist; if this is a real citation (not a format "
                        f"example with NN_xxx-style placeholders or a stale citation), "
                        f"fix or remove"
                    )
                else:
                    file_missing += 1
                    details.append(
                        f"  FILE: {gms_hint}:{start} (in {doc_short}) — full path does not exist; "
                        f"realization or directory may be fabricated"
                    )
                continue

        # Bare-basename fallback.
        # In module_NN.md docs (mod_num set): narrow to candidates under module NN.
        # In non-module docs (mod_num is None — cross_module/, core_docs/, etc.):
        # bare-basename citations cannot be safely resolved (no module scope).
        # Surface as ADVISORY warning, not error — many non-module docs contain
        # pedagogical examples (Bug_Taxonomy, Verification_Protocol, Infeasibility_
        # Debugging_Guide, adding_new_crop helper) showing the citation FORMAT;
        # those should not break the validator. Real bare-basename drift still
        # surfaces in the warnings stream so it gets seen.
        if not actual:
            if mod_num is None:
                # Non-module doc (cross_module/, core_docs/, reference/, helpers,
                # AGENT.md, README.md): an unresolved .gms cite here is ADVISORY,
                # not an error. It is EITHER a true bare basename OR a placeholder/
                # wildcard full path (e.g. modules/XX_.../ or modules/NN/*/) that
                # CITATION_RE can't parse (its prefix capture breaks on '.' / '*').
                # The `continue` is load-bearing: it keeps these out of the gated
                # file_missing bucket. Do NOT delete this branch (see BACKLOG C2-1).
                ambig += 1  # count in ambig bucket (same as other advisory warns)
                warnings.append(
                    f"  UNRESOLVED-NM: {gms_hint}:{start} (in {doc_short}) - unresolved "
                    f".gms citation in a non-module doc (a bare basename, or a placeholder/"
                    f"wildcard full path the resolver can't parse); if it is a real "
                    f"reference, use a concrete full path per MANDATE 16"
                )
                continue

            candidates = file_index.get(basename, [])
            mod_prefix = f'/{mod_num}_'
            mod_candidates = [c for c in candidates if mod_prefix in c]

            if '/' in gms_hint:
                # bare hint like "flexreg_apr16/equations.gms"
                realization_hint = os.path.dirname(gms_hint)
                narrowed = [c for c in mod_candidates if f'/{realization_hint}/' in c]
                if narrowed:
                    mod_candidates = narrowed
                else:
                    # The realization hint may actually be a CROSS-MODULE path (e.g.
                    # "11_costs/default" cited inside module_40.md). Resolve it against
                    # THAT module before declaring the file missing. Clear the candidate
                    # lists so the same-module basename fallback below does not overwrite
                    # the cross-module hit with the doc's-own-module file of the same name.
                    first_seg = realization_hint.split('/', 1)[0]
                    if (len(first_seg) > 3 and first_seg[:2].isdigit()
                            and first_seg[2] == '_'
                            and os.path.isfile(os.path.join(magpie_root, 'modules', gms_hint))):
                        actual = os.path.join(magpie_root, 'modules', gms_hint)
                        candidates = []
                        mod_candidates = []
                    else:
                        # not a resolvable cross-module path; do NOT walk-order rescue.
                        file_missing += 1
                        details.append(
                            f"  FILE: {gms_hint}:{start} (in {doc_short}) — bare hint with "
                            f"realization '{realization_hint}' but no matching file under "
                            f"module {mod_num}_* (and not a resolvable cross-module path)"
                        )
                        continue

            if mod_candidates:
                # Prefer the module's DEFAULT realization (config/default.cfg)
                # over walk-order. Resolving to the default is deterministic and
                # correct: a bare cite describes the default-compiled module.
                default_real = module_default_realization.get(mod_num)
                default_match = None
                if default_real:
                    for c in mod_candidates:
                        if f'/{default_real}/' in c:
                            default_match = c
                            break
                if default_match:
                    actual = default_match
                    # Deterministic — not a walk-order guess, so no AMBIG warning.
                else:
                    actual = mod_candidates[0]
                    # WARN only if still ambiguous after narrowing
                    if len(mod_candidates) > 1:
                        ambig += 1
                        relatives = [os.path.relpath(c, magpie_root) for c in mod_candidates]
                        warnings.append(
                            f"  AMBIG: {gms_hint}:{start} resolved to {os.path.relpath(actual, magpie_root)} "
                            f"by walk-order in {doc_short} — other candidates: {relatives[1:]}. "
                            f"Use full path per MANDATE 16."
                        )
            elif candidates:
                actual = candidates[0]

        if not actual:
            file_missing += 1
            details.append(f"  FILE: {gms_hint}:{start} (in {doc_short})")
            continue

        lines = get_lines(actual)
        total_lines = len(lines)

        # All listed lines must exist. Every cited (start, end) range is checked,
        # not just the primary; closes the Pattern-10 gap where comma-list
        # continuations (`:25,24,26`) silently dropped their 2nd..Nth line numbers.
        all_cited_in_range = all(
            rs <= total_lines and (re_ is None or re_ <= total_lines)
            for rs, re_ in line_ranges
        )
        existence_checks = []
        for ridx, (rs, re_) in enumerate(line_ranges):
            tag = 'start' if ridx == 0 else f'cite{ridx + 1}'
            existence_checks.append((rs, tag))
            if re_:
                existence_checks.append((re_, tag + '-end'))

        # Check each listed line. In non-module docs (mod_num=None), surface as
        # advisory; pedagogical format examples (e.g., `presolve.gms:123` in
        # README citation-format sections) are common.
        for line_num, label in existence_checks:
            if line_num > total_lines:
                delta = line_num - total_lines
                if mod_num is None:
                    ambig += 1
                    warnings.append(
                        f"  LINE-NM: {gms_hint}:{line_num} (file has {total_lines} lines, +{delta}, range-{label}) in {doc_short} — likely pedagogical example, but verify"
                    )
                else:
                    line_over += 1
                    details.append(
                        f"  LINE: {gms_hint}:{line_num} (file has {total_lines} lines, +{delta}, range-{label}) in {doc_short}"
                    )

        # Skip content checks on pedagogical docs (Bug_Taxonomy etc.) and
        # scaffolding-file cites (realization.gms / module.gms which are
        # $include directives, not variable-definition sources).
        if doc_short in PEDAGOGICAL_DOCS:
            if all_cited_in_range:
                valid += 1
            continue
        if os.path.basename(actual) in SCAFFOLDING_BASENAMES:
            if all_cited_in_range:
                valid += 1
            continue

        # Content-match check (Pattern 12 + R6 Phase 1 1d fingerprint hardening)
        if start <= total_lines and nearby_ids:
            # Tight window: cited start line ±5 (or start..end for ranges).
            # If a backticked identifier is NOT in this window, scan wider
            # (±50 lines) and report where it actually lives so the reviewer
            # can update the citation. Turns "advisory warn" into "warn with
            # suggested fix".
            tight_start = max(1, start - 5)
            tight_end = min(total_lines, (end if end else start) + 5)
            # tight_text spans +/-5 around EVERY cited line (primary + comma-list
            # continuations), so an identifier near ANY listed line passes the
            # fingerprint; a `:22,49,60,71` cite legitimately names content at all
            # four. (tight_start/tight_end stay the PRIMARY window for messages.)
            near_idx = set()
            for rs, re_ in line_ranges:
                ws = max(1, rs - 5)
                we = min(total_lines, (re_ if re_ else rs) + 5)
                near_idx.update(range(ws, we + 1))
            tight_text = "\n".join(lines[i - 1] for i in sorted(near_idx) if i - 1 < len(lines))

            # STRICT-LINE check (R25 Phase 1 follow-up): for declarations.gms
            # and input.gms files, the identifier should be at EXACTLY the
            # cited line (these files are one-identifier-per-line by convention).
            # Catches the off-by-1/2 drifts that fall within the ±5 fingerprint
            # window — R25 Q2-B1/B2 class (s80_counter, s80_resolve_option).
            # Gated to:
            #   - single-line cites (range cites span multiple identifiers
            #     legitimately)
            #   - cites with at least realization-level path specificity
            #     (any "/" in gms_hint, e.g. "modules/X/Y/declarations.gms"
            #     or "nlp_apr17/declarations.gms"). Bare-basename cites
            #     ("declarations.gms" alone) can be rescued to the wrong
            #     realization (e.g. nlp_par when the doc means nlp_apr17),
            #     so we skip STRICT to avoid FPs from rescue ambiguity.
            basename = os.path.basename(actual)
            is_strict_target = basename in ('declarations.gms', 'input.gms')
            is_single_line = end is None
            is_path_specific = '/' in gms_hint
            if is_strict_target and is_single_line and is_path_specific and start <= total_lines:
                # The exact single lines this cite names: the primary plus any
                # comma-list continuation that is itself a single line. An
                # identifier is correctly cited if it sits at ANY of them, since
                # declarations.gms is one-identifier-per-line (e.g. `:25,24,26`
                # naming three vars at 25/24/26 is correct, not drift). Range
                # continuations are excluded (a span, not a single-line anchor).
                strict_lines = [start] + [rs for rs, re_ in extra if re_ is None]
                for gid in nearby_ids:
                    at_cited = any(
                        s - 1 < len(lines)
                        and re.search(rf"\b{re.escape(gid)}\b", lines[s - 1])
                        for s in strict_lines
                    )
                    if not at_cited:
                        # Identifier at NONE of the cited lines. Find where it
                        # actually lives (within wider window so we suggest
                        # a fix even when fingerprint would also flag it).
                        scan_start = max(1, start - 5)
                        scan_end = min(total_lines, start + 5)
                        actual_lines = [
                            i for i in range(scan_start, scan_end + 1)
                            if i - 1 < len(lines)
                            and re.search(rf"\b{re.escape(gid)}\b", lines[i - 1])
                        ]
                        if actual_lines:
                            closest = min(actual_lines, key=lambda x: abs(x - start))
                            delta = closest - start
                            sign = "+" if delta > 0 else ""
                            content_miss += 1
                            warnings.append(
                                f"  STRICT: `{gid}` cited at {gms_hint}:{start} but "
                                f"identifier is at line {closest} ({sign}{delta}). "
                                f"Strict-line check for {basename} — update citation to ~:{closest}."
                            )

            # EQUATION-NAME ADJACENT-BLOCK DRIFT pre-flag (Check 5; Task 3 / R25
            # follow-up). The +/-5 fingerprint loop below passes a cite whenever
            # the identifier appears ANYWHERE within +/-5 lines, so a single-line
            # cite that drifted onto a similar-content NEIGHBOR equation still
            # passes silently (BACKLOG: "too tolerant of similar-content
            # neighbors"). Equation NAMES (qNN_*) are defined EXACTLY ONCE per
            # equations.gms, so unlike vm_/pm_/scalars (which recur in every
            # using-equation, making the nearest occurrence ambiguous) an equation
            # name's definition line is an unambiguous anchor.
            #
            # CRITICAL FP guard (verified on corpus 2026-06-05): docs frequently
            # and CORRECTLY cite a BODY line of a multi-line equation to pin where
            # a variable is consumed/produced, while naming that equation for
            # context (e.g. module_18.md cites `q50_nr_withdrawals` at :40/:41 to
            # show where vm_res_biomass_ag/_bg are read; module_30.md cites
            # `q29_carbon` at :31 where vm_carbon_stock_croparea is read). The
            # cited line is INSIDE the named equation's own [def..terminator] span
            # there, so it is NOT drift. We therefore flag ONLY when the cited line
            # lands OUTSIDE the named equation's span entirely (i.e. on a neighbor
            # block) yet the name is still within +/-5. That is unambiguous drift.
            #   * declarations.gms/input.gms: handled by the STRICT block above.
            #   * ranges: excluded (legitimately span comment + equation).
            #   * vm_/pm_/etc.: excluded (recurrence makes drift ambiguous).
            is_eqname_file = (basename not in ('declarations.gms', 'input.gms')
                              and basename not in SCAFFOLDING_BASENAMES)
            # `not extra`: a comma-list enumerates multiple lines deliberately, so
            # single-line adjacent-block drift does not apply to it.
            if is_eqname_file and is_single_line and not extra and start <= total_lines:
                for gid in nearby_ids:
                    if not EQ_NAME_RE.match(gid):
                        continue
                    # Definition line(s) of this equation name within +/-5. In
                    # equations.gms the name appears once (at the `qNN_(dom) ..`
                    # definition); empty => out of window, left to the CONTENT scan.
                    occ = [
                        i for i in range(tight_start, tight_end + 1)
                        if i - 1 < len(lines)
                        and re.search(rf"\b{re.escape(gid)}\b", lines[i - 1])
                    ]
                    if not occ or any(abs(o - start) <= 1 for o in occ):
                        continue  # not nearby, or a fencepost off-by-one (not drift)
                    def_line = min(occ, key=lambda x: abs(x - start))
                    # Span the named equation (def line -> its `;` terminator).
                    span_end = eq_span_end(lines, def_line, total_lines)
                    if def_line <= start <= span_end:
                        continue  # cited line is inside the named equation's body
                    delta = def_line - start
                    sign = "+" if delta > 0 else ""
                    content_miss += 1
                    warnings.append(
                        f"  DRIFT: `{gid}` cited at {gms_hint}:{start} lands outside "
                        f"its equation block (defined at {def_line}..{span_end}, "
                        f"{sign}{delta} from the cited line) yet within the +/-5 "
                        f"fingerprint window; likely an adjacent-block citation "
                        f"drift. Update citation to ~:{def_line}."
                    )

            for gid in nearby_ids:
                if gid in tight_text:
                    continue
                # Wider scan ±50 lines for the actual location of `gid`
                wide_start = max(1, start - 50)
                wide_end = min(total_lines, (end if end else start) + 50)
                actual_lines = []
                for i in range(wide_start, wide_end + 1):
                    if i - 1 < len(lines) and re.search(rf"\b{re.escape(gid)}\b", lines[i - 1]):
                        actual_lines.append(i)
                # EQUATION-BODY-CITE guard (same rationale as Check 5; verified on
                # corpus 2026-06-05). A doc may NAME an equation but cite a BODY
                # line deeper than +/-5 into its block to pin a consumed/produced
                # variable; e.g. module_54.md names `q11_cost_reg` while citing
                # :25 (where vm_p_fert_costs is summed), though q11_cost_reg is
                # DEFINED at :15. The name then sits >5 lines from the cited line,
                # so the fingerprint misses it, yet the cite is CORRECT, not drift.
                # If gid is an equation name whose [def..terminator] span CONTAINS
                # the cited line (and the whole cited range), the cite is
                # in-equation: skip the CONTENT warning. (vm_/pm_ are NOT
                # span-anchored, so they remain subject to the normal +/-5 check.)
                if EQ_NAME_RE.match(gid) and actual_lines:
                    in_equation = False
                    for d in actual_lines:
                        se = eq_span_end(lines, d, total_lines)
                        if d <= start <= se and (not end or end <= se):
                            in_equation = True
                            break
                    if in_equation:
                        continue  # legitimate in-equation body-line cite, not drift
                content_miss += 1
                if actual_lines:
                    # Report the closest occurrence + delta
                    closest = min(actual_lines, key=lambda x: abs(x - start))
                    delta = closest - start
                    sign = "+" if delta > 0 else ""
                    warnings.append(
                        f"  CONTENT: `{gid}` not found within {gms_hint}:{tight_start}-{tight_end} "
                        f"(cited from {doc_short}); actual occurrence(s) at line(s) "
                        f"{actual_lines[:3]}{'...' if len(actual_lines) > 3 else ''} "
                        f"(closest delta {sign}{delta} from cited start). "
                        f"Likely Pattern 10/12 citation drift — update citation to ~:{closest}."
                    )
                else:
                    warnings.append(
                        f"  CONTENT: `{gid}` not found within {gms_hint}:{tight_start}-{tight_end} "
                        f"(cited from {doc_short}); also absent ±50 lines around start. "
                        f"Possible identifier rename, file restructure, or false-positive "
                        f"(identifier referenced by name in prose, not in cited block)."
                    )

        if all_cited_in_range:
            valid += 1

    total = valid + file_missing + line_over
    issues = file_missing + line_over

    if issues > 0:
        print(f"Citation check: {issues} issues ({file_missing} missing files, {line_over} out-of-range lines)")
        print(f"Valid: {valid}/{total}")
        for d in sorted(set(details))[:20]:
            print(d)
        if len(details) > 20:
            print(f"  ... and {len(details) - 20} more")
        # Also print warnings (warn-only categories) but don't change exit code
        if warnings:
            print(f"Plus warnings: {ambig} ambig, {content_miss} content-mismatch (advisory only)")
            for w in sorted(set(warnings))[:5]:
                print(w)
            if len(warnings) > 5:
                print(f"  ... and {len(warnings) - 5} more advisory warnings")
        sys.exit(1)
    else:
        print(f"File:line citations verified: {valid}/{total} valid")
        if warnings:
            # Warnings (bare-basename ambiguity, possible Pattern 12 mismatch) are
            # advisory; do not fail the validator. Surface counts inline so users
            # can act on them without blocking the main pipeline.
            print(f"Advisory warnings: {ambig} non-module/ambiguous citation notes, {content_miss} possible Pattern-12 content mismatch (not counted as errors)")
            for w in sorted(set(warnings))[:5]:
                print(w)
            if len(warnings) > 5:
                print(f"  ... and {len(warnings) - 5} more advisory warnings")
        sys.exit(0)


if __name__ == '__main__':
    main()
