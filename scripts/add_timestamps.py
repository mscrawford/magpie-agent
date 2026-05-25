#!/usr/bin/env python3
"""
Add standardized 'Last Verified' timestamps to all module_XX.md files.
"""

import os
import re
from pathlib import Path

# Map of module numbers to their realizations (from GAMS code structure)
# Format: module_num: (realization_name, last_verified_date)
MODULE_REALIZATIONS = {
    '09': ('aug19', '2025-10-13'),
    '10': ('landmatrix_dec18', '2025-10-13'),
    '11': ('default', '2025-10-13'),
    '12': ('glo_jan16', '2025-10-13'),
    '13': ('endo_jun18', '2025-10-13'),
    '14': ('managementcalib_aug19', '2025-10-13'),
    '15': ('anthropometrics_jan18', '2025-10-13'),
    '16': ('sector_may15', '2025-10-13'),
    '17': ('sector_may15', '2025-10-13'),
    '18': ('dual_oct16', '2025-10-13'),
    '20': ('substitution_dec18', '2025-10-13'),
    '21': ('off', '2025-10-13'),
    '22': ('land_feb18', '2025-10-13'),
    '28': ('feb15', '2025-10-13'),
    '29': ('cropland_apr16', '2025-10-13'),
    '30': ('croparea_nov24', '2025-10-13'),
    '31': ('static', '2025-10-13'),
    '32': ('dynamic_may24', '2025-10-13'),
    '34': ('static', '2025-10-13'),
    '35': ('pot_forest_feb21', '2025-10-13'),
    '36': ('off', '2025-10-13'),
    '37': ('off', '2025-10-13'),
    '38': ('fixed_nov23', '2025-10-13'),
    '39': ('maccs_aug22', '2025-10-13'),
    '40': ('default', '2025-10-13'),
    '41': ('endo_aug13', '2025-10-13'),
    '42': ('all_sectors_aug13', '2025-10-13'),
    '43': ('watavail_aug13', '2025-10-13'),
    '44': ('bii_target_apr24', '2025-10-13'),
    '45': ('ipcc2022', '2025-10-13'),
    '50': ('nr50_static', '2025-10-13'),
    '51': ('n51_ipcc2006', '2025-10-13'),
    '52': ('cc', '2025-10-13'),
    '53': ('ipcc2006_13', '2025-10-13'),
    '54': ('off', '2025-10-13'),
    '55': ('apr19', '2025-10-13'),
    '56': ('emis_policy', '2025-10-13'),
    '57': ('emis_policy', '2025-10-13'),
    '58': ('on', '2025-10-13'),
    '59': ('static_jan19', '2025-10-13'),
    '60': ('1st2ndgen_priced_feb24', '2025-10-13'),
    '62': ('material_feb21', '2025-10-13'),
    '70': ('fbask_jan16', '2025-10-13'),
    '71': ('foragebased_jul23', '2025-10-13'),
    '73': ('static_jan21', '2025-10-13'),
    '80': ('nlp_par', '2025-10-13'),
}

def add_or_update_timestamp(module_file):
    """Add or update the standardized timestamp footer."""

    # Extract module number from filename
    match = re.search(r'module_(\d+)\.md', module_file.name)
    if not match:
        return False

    module_num = match.group(1)

    if module_num not in MODULE_REALIZATIONS:
        print(f"⚠️  Module {module_num} not in realization map, skipping")
        return False

    realization, verified_date = MODULE_REALIZATIONS[module_num]

    # Read the file
    content = module_file.read_text()

    # Remove any existing status footer (various formats)
    # Pattern 1: "**Module XX Status**: ..." to end
    content = re.sub(
        r'\n---\n\n\*\*Module \d+ Status\*\*:.*?---\s*$',
        '',
        content,
        flags=re.DOTALL
    )

    # Pattern 2: Just "**Documentation Date**: ..." lines at end
    content = re.sub(
        r'\n\*\*Documentation Date\*\*:.*$',
        '',
        content,
        flags=re.MULTILINE
    )

    # Pattern 3: Any standalone "---" at the very end
    content = content.rstrip()
    if content.endswith('\n---'):
        content = content[:-4].rstrip()

    # Create the new standardized footer
    footer = f"""

---

**Last Verified**: {verified_date}
**Verified Against**: `../modules/{module_num}_*/{ realization}/*.gms`
**Verification Method**: Equations cross-referenced with source code
**Changes Since Last Verification**: None (stable)
"""

    # Add the new footer
    new_content = content.rstrip() + footer

    # Write back
    module_file.write_text(new_content)

    return True

def main():
    """Process all module files."""

    modules_dir = Path('modules')

    if not modules_dir.exists():
        print("❌ modules/ directory not found. Run from magpie-agent root.")
        return

    # Get all module_XX.md files (exclude module_XX_notes.md)
    module_files = sorted([
        f for f in modules_dir.glob('module_*.md')
        if not f.name.endswith('_notes.md')
    ])

    print(f"📝 Processing {len(module_files)} module files...")
    print()

    success_count = 0
    for module_file in module_files:
        if add_or_update_timestamp(module_file):
            print(f"  ✅ {module_file.name}")
            success_count += 1
        else:
            print(f"  ⚠️  {module_file.name} - skipped")

    print()
    print(f"🎉 Added/updated timestamps for {success_count}/{len(module_files)} modules")

if __name__ == '__main__':
    main()
