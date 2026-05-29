# SMOKE TEST — module_52.md consumer claim for `pm_carbon_density_plantation_ac_uncalib`

Date: 2026-05-29
Purpose: validate the doc-audit pipeline plumbing with one real verification.
Develop worktree (read-only): `/tmp/magpie_develop_ro`

## 1. The doc claim (module_52.md)

`modules/module_52.md:291` (the "Writes ... uncalibrated copies" bullet):

> **Writes** `pm_carbon_density_secdforest_ac_uncalib`, `pm_carbon_density_plantation_ac_uncalib`
> (preserved for new-establishment contexts; consumed by **Module 32 afforestation+NDC and Module 29 tree cover**;
> `pm_carbon_density_secdforest_ac_uncalib` *also* consumed by Module 35
> `modules/35_natveg/pot_forest_may24/presolve.gms:117`)

Supporting detail at `module_52.md:277-279`:
- Module 32 (Forestry): `presolve.gms:58,60` (aff) and `:69` (ndc)
- Module 29 (Cropland): `preloop.gms:46,48` (tree cover)

So the doc claims the **plantation** uncalib is consumed by **M32 and M29 only**.
The only mention of **M35** on line 291 is explicitly tied to the **secdforest** uncalib, NOT the plantation one.

The advisory checker flagged this line as "lists M35" for the plantation parameter. That is a
**false positive**: the checker matched "Module 35" co-occurring on the same line as
`pm_carbon_density_plantation_ac_uncalib`, but the M35 citation in that sentence belongs to
`pm_carbon_density_secdforest_ac_uncalib`.

## 2. Develop reality

Every `.gms` reference to `pm_carbon_density_plantation_ac_uncalib` under `/tmp/magpie_develop_ro/modules/`:

| File | Line | Role | Module |
|------|------|------|--------|
| `52_carbon/normal_dec17/declarations.gms` | 13 | declaration | 52 |
| `52_carbon/normal_dec17/start.gms` | 44 | write (saves uncalib copy) | 52 |
| `29_cropland/detail_apr24/preloop.gms` | 48 | read (`p29_carbon_density_ac = ...`) | 29 |
| `32_forestry/dynamic_may24/presolve.gms` | 61 | read (`p32_carbon_density_ac(...,"aff",...) = ...`) | 32 |

Non-`.gms` hit (informational, not a consumer): `29_cropland/simple_apr24/not_used.txt:7`
marks the parameter `input,not needed` for the `simple_apr24` realization.

**Consumer modules (excluding the owning module 52): {29, 32}.**

### M35 specifically — does any `35_*` `.gms` reference the plantation uncalib?
**NO.** Confirmed by two independent methods, with a positive control to prove the search works:
- `35_natveg` contains 10 `.gms` files.
- Positive control: `pm_carbon_density_secdforest_ac_uncalib` returns 3 hits in
  `35_natveg/pot_forest_may24/presolve.gms` (lines 117, 242, 251) — so the directory and the
  search tooling are working.
- Target: `pm_carbon_density_plantation_ac_uncalib` returns **0 hits** in `35_natveg` via both
  `rg` (exit 1) and `find ... -exec grep` (no output).

This matches the doc exactly: M35 consumes the *secdforest* uncalib (`presolve.gms:117`), not the
*plantation* uncalib.

## 3. Exact commands used

```bash
which rg
# -> /opt/homebrew/bin/rg   (ripgrep available)

# All references, method A (find + grep, batched):
find /tmp/magpie_develop_ro/modules -name '*.gms' -exec grep -Hn 'pm_carbon_density_plantation_ac_uncalib' {} +

# All references, method B (ripgrep cross-check):
rg -n 'pm_carbon_density_plantation_ac_uncalib' /tmp/magpie_develop_ro/modules/

# M35 probe, method A (ripgrep, count):
rg -c 'pm_carbon_density_plantation_ac_uncalib' /tmp/magpie_develop_ro/modules/35_natveg/   # exit 1, no match

# M35 probe, method B (find + grep, semicolon form to avoid batch-exit masking):
find /tmp/magpie_develop_ro/modules/35_natveg -name '*.gms' -exec grep -Hn 'pm_carbon_density_plantation_ac_uncalib' {} \;   # no output

# M35 positive control (proves grep works in 35_natveg):
find /tmp/magpie_develop_ro/modules/35_natveg -name '*.gms' -exec grep -Hn 'pm_carbon_density_secdforest_ac_uncalib' {} \;   # 3 hits
```

Note on tooling: the bare `grep -r` warning held in spirit — when `find ... -exec grep {} +`
finds nothing in its final batch it returns exit 1, which silently aborted the *rest* of a
compound (`&&`/`;`-chained) command and truncated later output. Running each probe as an
isolated command, plus a positive control, was what disambiguated "no match" from "command
aborted early." Both `rg` and `find+grep` agreed once isolated.

## 4. Verdict

**Doc is CORRECT. Advisory flag is a FALSE POSITIVE.**

- `pm_carbon_density_plantation_ac_uncalib` is consumed (outside owner M52) by **M29 and M32 only**.
- **No `35_*` `.gms` file references it.** The M35 citation on `module_52.md:291` correctly
  refers to the *secdforest* uncalib, not the plantation one. The checker should distinguish
  which of the two adjacent parameter names a co-located "Module 35" citation attaches to.

Pipeline plumbing (read doc -> verify in develop -> cross-check two methods -> write findings)
works end to end.
