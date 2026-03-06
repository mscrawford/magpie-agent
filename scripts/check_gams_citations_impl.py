#!/usr/bin/env python3
"""Verify file:line citations in AI docs against GAMS code.

Checks that file.gms:NN references in module docs point to files that exist
and have at least NN lines. Reports missing files and out-of-range lines.
"""

import subprocess, re, os, sys
from collections import defaultdict

def main():
    agent_dir = sys.argv[1]
    magpie_root = sys.argv[2]

    # Build file index: basename -> [full_paths] for fast lookup
    file_index = defaultdict(list)
    for root, dirs, files in os.walk(os.path.join(magpie_root, 'modules')):
        for f in files:
            if f.endswith('.gms'):
                file_index[f].append(os.path.join(root, f))
    for root, dirs, files in os.walk(os.path.join(magpie_root, 'core')):
        for f in files:
            if f.endswith('.gms'):
                file_index[f].append(os.path.join(root, f))

    # Extract citations from AI docs
    result = subprocess.run(
        ['rg', '-n', r'\w+\.gms:\d+', os.path.join(agent_dir, 'modules/')],
        capture_output=True, text=True
    )

    # Parse and deduplicate
    citations = {}
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        m = re.match(r'^(.+/module_(\d+)\w*\.md):(\d+):(.+)', line)
        if not m:
            continue
        doc_file = m.group(1)
        mod_num = m.group(2)
        context = m.group(4)

        refs = re.findall(r'((?:core/|modules/[\w/]+/)?[\w/]+\.gms):(\d+)', context)
        for gms_hint, line_num in refs:
            key = (doc_file, mod_num, gms_hint, int(line_num))
            if key not in citations:
                citations[key] = True

    # Verify each citation
    valid = 0
    file_missing = 0
    line_over = 0
    details = []

    for (doc_file, mod_num, gms_hint, gms_line) in sorted(citations.keys()):
        actual = None
        basename = os.path.basename(gms_hint)

        if gms_hint.startswith('core/') or gms_hint.startswith('modules/'):
            full = os.path.join(magpie_root, gms_hint)
            if os.path.isfile(full):
                actual = full
        
        if not actual:
            # Search by basename within the module directory
            candidates = file_index.get(basename, [])
            mod_prefix = f'/{mod_num}_'
            mod_candidates = [c for c in candidates if mod_prefix in c]
            if mod_candidates:
                actual = mod_candidates[0]
            elif candidates:
                actual = candidates[0]  # fallback: any match

        if not actual:
            file_missing += 1
            doc_short = os.path.basename(doc_file)
            details.append(f"  FILE: {gms_hint}:{gms_line} (in {doc_short})")
            continue

        with open(actual, 'r') as f:
            total_lines = sum(1 for _ in f)

        if gms_line > total_lines:
            line_over += 1
            delta = gms_line - total_lines
            doc_short = os.path.basename(doc_file)
            details.append(f"  LINE: {gms_hint}:{gms_line} (file has {total_lines} lines, +{delta}) in {doc_short}")
        else:
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
        sys.exit(1)
    else:
        print(f"File:line citations verified: {valid}/{total} valid")
        sys.exit(0)

if __name__ == '__main__':
    main()
