#!/usr/bin/env python3
"""Phase B-prime: inject ONE inverted code-fact into a full copy of each real doc.

Copies live in /tmp/r51_longdoc/ (repo docs are NEVER modified). Each injected
doc has exactly one planted error; an isolated auditor then audits the WHOLE doc
(no pointing question) and we measure whether it FINDS the injection -> the
production-relevant find-rate, vs the per-claim 100%.

Ground truth verified @ea383032d in Phase 0. The find/replace strings are exact
substrings of the current repo docs (asserted present before injection).
"""
import os, shutil, json

REPO = "<magpie-agent>"
OUT = "/tmp/r51_longdoc"
if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)

# doc_id: (repo_relpath, [(find, replace), ...], injected_bug, code_truth, expected_class)
INJ = {
  "module_30": ("modules/module_30.md", [
      ('**Default realization**: `simple_apr24` (per `config/default.cfg`: `cfg$gms$croparea <- "simple_apr24"`)',
       '**Default realization**: `detail_apr24` (per `config/default.cfg`: `cfg$gms$croparea <- "detail_apr24"`)'),
      ('**Alternative**: `detail_apr24`', '**Alternative**: `simple_apr24`'),
    ],
    "croparea(30) default stated as detail_apr24",
    "croparea default is simple_apr24 (config/default.cfg); detail_apr24 is the non-default sibling.",
    "wrong realization as default (Critical)"),

  "module_51": ("modules/module_51.md", [
      ('declared by Module 55 AWMS', 'declared by Module 50 NR Soil Budget'),
    ],
    "vm_manure_recycling stated as declared by Module 50",
    "vm_manure_recycling is declared+populated in Module 55 (awms); Module 50 only reads it.",
    "producer mis-attribution (Major/Critical)"),

  "module_42": ("modules/module_42.md", [
      ('**Realization**: `all_sectors_aug13` (more comprehensive than `agr_sector_aug13`)',
       '**Realization**: `agr_sector_aug13` (more comprehensive than `all_sectors_aug13`)'),
      ('> ⚙️ **Default Realization**: `all_sectors_aug13`',
       '> ⚙️ **Default Realization**: `agr_sector_aug13`'),
      ('`cfg$gms$water_demand <- "all_sectors_aug13"`', '`cfg$gms$water_demand <- "agr_sector_aug13"`'),
    ],
    "water_demand(42) default stated as agr_sector_aug13",
    "water_demand default is all_sectors_aug13 (config/default.cfg); agr_sector_aug13 is non-default.",
    "wrong realization as default (Critical)"),

  "module_70": ("modules/module_70.md", [
      ('# Module 70: Livestock (fbask_jan16)', '# Module 70: Livestock (fbask_jan16_sticky)'),
      ('**Realization**: `fbask_jan16` (feed basket-based, January 2016)',
       '**Realization**: `fbask_jan16_sticky` (feed basket-based with stickiness, January 2016)'),
    ],
    "livestock(70) default stated as fbask_jan16_sticky",
    "livestock default is fbask_jan16 (config/default.cfg); fbask_jan16_sticky is non-default.",
    "wrong realization as default (Critical)"),

  "module_13": ("modules/module_13.md", [
      ('is now at cluster level (j) rather than super-region level (h)',
       'is now at super-region level (h) rather than cluster level (j)'),
    ],
    "vm_tau stated as at super-region level (h)",
    "vm_tau(j,tautype) is at CLUSTER level j (13_tc/endo_jan22/declarations.gms:13), not super-region h.",
    "wrong index domain / scope (Major)"),

  "module_38": ("modules/module_38.md", [
      ('consumed by Module 11 (via `q11_cost_reg`, both factors)',
       'consumed by Module 17 (via `q17_prod_reg`, both factors)'),
    ],
    "vm_cost_prod_crop stated as consumed by Module 17",
    "vm_cost_prod_crop is consumed by Module 11 (q11_cost_reg) and Module 36; not Module 17.",
    "wrong consumer attribution (Major)"),

  "carbon_balance": ("cross_module/carbon_balance_conservation.md", [
      ('All populated slices flow to Module 52 and Module 56',
       'All populated slices flow to Module 52, which then forwards them to Module 56'),
    ],
    "soilc/carbon stock stated as serial M52 -> M56 hand-off",
    "M52 and M56 are PARALLEL readers of vm_carbon_stock; M56 reads it directly (q56_emis_pricing_co2), not via M52.",
    "invented serial data-flow (Major)"),
}

key = {"phase": "B-prime", "purpose": "find-in-long-doc FNR (does the auditor FIND the injected bug with no pointing question)", "docs": {}}
for did, (rel, repl, bug, truth, klass) in INJ.items():
    src = os.path.join(REPO, rel)
    text = open(src).read()
    for find, rep in repl:
        n = text.count(find)
        assert n == 1, f"{did}: find-string appears {n}x (want 1): {find[:60]!r}"
        text = text.replace(find, rep)
    base = os.path.basename(rel)
    ddir = os.path.join(OUT, did); os.makedirs(ddir)
    with open(os.path.join(ddir, base), "w") as fh:
        fh.write(text)
    key["docs"][did] = {"doc_file": base, "injected_bug": bug, "code_truth": truth,
                        "expected_class": klass, "n_edits": len(repl)}
    print(f"  {did}: injected '{bug}' into {base} ({len(repl)} edit(s))")

json.dump(key, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "longdoc_key.json"), "w"), indent=1)
print(f"\nWrote {len(INJ)} injected docs to {OUT}; key -> longdoc_key.json")
