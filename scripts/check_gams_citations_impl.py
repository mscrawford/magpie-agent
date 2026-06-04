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

Reports:
  FILE: missing file
  LINE: out-of-range line (start or end of range)
  AMBIG: bare-basename with multiple-realization ambiguity (WARN)
  CONTENT: identifier not found near cited line (WARN, content mismatch)
"""

import subprocess, re, os, sys, shutil, tempfile, textwrap
from collections import defaultdict


# Match a citation followed by an OPTIONAL range end:
#   `file.gms:50`        → start=50, end=None
#   `file.gms:50-75`     → start=50, end=75
CITATION_RE = re.compile(r'((?:core/|modules/[\w/]+/)?[\w/]+\.gms):(\d+)(?:-(\d+))?')

# GAMS identifier classes (used by Pattern 12 content check)
GAMS_ID_RE = re.compile(r'`((?:vm|pm|v|p|i|f|s|c|cm|sm|im|fm|pcm|ic|ov|oq|q)\d*_[a-zA-Z][\w]*)`')

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

        # v2/declarations.gms — 85 lines (default realization)
        with open(os.path.join(v2_dir, 'declarations.gms'), 'w') as f:
            for i in range(1, 86):
                f.write(f'* line {i}\n')

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

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    if ok:
        print("SELF-TEST PASS: Check 17 (file:line citations)")
        print("  [A] Out-of-range cite in off/ (18 lines) correctly flagged as LINE error")
        print("  [B] Bare-basename cite at line 80 correctly resolves to default v2/ "
              "(85 lines) and passes — f4f44b0 bare-cite resolution intact")
        print("  [C] Full-path cite to v2/ at line 80 correctly passes")
        return 0
    else:
        print("SELF-TEST FAIL: one or more assertions failed (see above)")
        return 1


def main():
    if '--self-test' in sys.argv:
        sys.exit(self_test())

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

            key = (doc_file, mod_num, gms_hint, start, end)
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
        (doc_file, mod_num, gms_hint, start, end), _ = item
        return (doc_file, mod_num, gms_hint, start, end if end is not None else -1)

    for (doc_file, mod_num, gms_hint, start, end), nearby_ids in sorted(citations.items(), key=sort_key):
        actual = None
        basename = os.path.basename(gms_hint)
        doc_short = os.path.basename(doc_file)

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
                ambig += 1  # count in ambig bucket (same as other advisory warns)
                warnings.append(
                    f"  BARE: {gms_hint}:{start} (in {doc_short}) — bare-basename "
                    f"citation in non-module doc; if this is a real reference "
                    f"(not a pedagogical example), use full path per MANDATE 16"
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

        # Check both start and end of range. In non-module docs (mod_num=None),
        # surface as advisory — pedagogical format examples (e.g.,
        # `presolve.gms:123` in README citation-format sections) are common.
        for line_num, label in [(start, 'start')] + ([(end, 'end')] if end else []):
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
            if start <= total_lines and (not end or end <= total_lines):
                valid += 1
            continue
        if os.path.basename(actual) in SCAFFOLDING_BASENAMES:
            if start <= total_lines and (not end or end <= total_lines):
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
            tight_text = "\n".join(lines[tight_start - 1:tight_end])

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
                cited_line_text = lines[start - 1] if start - 1 < len(lines) else ""
                for gid in nearby_ids:
                    if not re.search(rf"\b{re.escape(gid)}\b", cited_line_text):
                        # Identifier missing from cited line. Find where it
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

        if start <= total_lines and (not end or end <= total_lines):
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
            print(f"Advisory warnings: {ambig} bare-basename ambiguity, {content_miss} possible Pattern-12 content mismatch (not counted as errors)")
            for w in sorted(set(warnings))[:5]:
                print(w)
            if len(warnings) > 5:
                print(f"  ... and {len(warnings) - 5} more advisory warnings")
        sys.exit(0)


if __name__ == '__main__':
    main()
