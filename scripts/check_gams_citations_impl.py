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

import subprocess, re, os, sys
from collections import defaultdict


# Match a citation followed by an OPTIONAL range end:
#   `file.gms:50`        → start=50, end=None
#   `file.gms:50-75`     → start=50, end=75
CITATION_RE = re.compile(r'((?:core/|modules/[\w/]+/)?[\w/]+\.gms):(\d+)(?:-(\d+))?')

# GAMS identifier classes (used by Pattern 12 content check)
GAMS_ID_RE = re.compile(r'`((?:vm|pm|v|p|i|f|s|c|cm|sm|im|fm|pcm|ic|ov|oq|q)\d*_[a-zA-Z][\w]*)`')


def main():
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

    # Extract citations + nearby context from AI docs
    result = subprocess.run(
        ['rg', '-n', r'\w+\.gms:\d+', os.path.join(agent_dir, 'modules/')],
        capture_output=True, text=True
    )

    citations = {}  # (doc_file, mod_num, gms_hint, start, end) -> {nearby_ids}
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        m = re.match(r'^(.+/module_(\d+)\w*\.md):(\d+):(.+)', line)
        if not m:
            continue
        doc_file, mod_num, _doc_line, context = m.group(1), m.group(2), m.group(3), m.group(4)

        # Find all citations on this line so we can scope each nearby_ids window
        # only to the text between this cite and the previous one (avoids picking
        # up identifiers that belong to a sibling citation in the same prose).
        cite_matches = list(CITATION_RE.finditer(context))
        for idx, cit_match in enumerate(cite_matches):
            gms_hint = cit_match.group(1)
            start = int(cit_match.group(2))
            end = int(cit_match.group(3)) if cit_match.group(3) else None

            # Capture nearby backticked GAMS identifiers in a tighter window:
            # back to the previous cite (or 40 chars, whichever is closer) and
            # forward only 10 chars (citations typically follow their subject).
            prev_end = cite_matches[idx - 1].end() if idx > 0 else 0
            window_start = max(prev_end, cit_match.start() - 40)
            window_end = min(len(context), cit_match.end() + 10)
            window = context[window_start:window_end]
            nearby_ids = set(GAMS_ID_RE.findall(window))

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
        if gms_hint.startswith('core/') or gms_hint.startswith('modules/'):
            full = os.path.join(magpie_root, gms_hint)
            if os.path.isfile(full):
                actual = full
            else:
                file_missing += 1
                details.append(
                    f"  FILE: {gms_hint}:{start} (in {doc_short}) — full path does not exist; "
                    f"realization or directory may be fabricated"
                )
                continue

        # Bare-basename fallback: walk_index by basename within module number.
        # Only reached when gms_hint is a bare basename (no modules/ or core/
        # prefix). A bare-basename hint with a single internal slash is treated
        # as `realization/file.gms` and narrowed by realization.
        if not actual:
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
                    # Realization hint present but doesn't match any candidate —
                    # do NOT walk-order rescue; surface as FILE issue.
                    file_missing += 1
                    details.append(
                        f"  FILE: {gms_hint}:{start} (in {doc_short}) — bare hint with "
                        f"realization '{realization_hint}' but no matching file under "
                        f"module {mod_num}_*"
                    )
                    continue

            if mod_candidates:
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

        # Check both start and end of range
        for line_num, label in [(start, 'start')] + ([(end, 'end')] if end else []):
            if line_num > total_lines:
                line_over += 1
                delta = line_num - total_lines
                details.append(
                    f"  LINE: {gms_hint}:{line_num} (file has {total_lines} lines, +{delta}, range-{label}) in {doc_short}"
                )

        # Content-match check (Pattern 12)
        if start <= total_lines and nearby_ids:
            # Window: cited start line ±5 (or start..end for ranges)
            check_start = max(1, start - 5)
            check_end = min(total_lines, (end if end else start) + 5)
            window_text = "\n".join(lines[check_start - 1:check_end])
            for gid in nearby_ids:
                if gid not in window_text:
                    # Only WARN — false positives possible (identifier referenced
                    # by name in prose but not in the cited equation block)
                    content_miss += 1
                    warnings.append(
                        f"  CONTENT: `{gid}` not found within {gms_hint}:{check_start}-{check_end} "
                        f"(cited from {doc_short}). Possible Pattern 12 citation mismatch."
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
