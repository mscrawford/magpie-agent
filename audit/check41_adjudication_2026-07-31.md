# Check 41 — adjudication table (2026-07-31)

**Status: FOR REVIEW. No doc was edited from this table.** These are 47 module-level
judgments about other people's modules; Mike reviews the *decisions*, not a fait
accompli. Produced by the autonomous overnight run under an explicit instruction to
emit a table rather than corrections.

**Generated after** the owner-less-vars fix landed (commit `179ddeb`), because that fix
moves the finding set. Pre-fix the numbers were 19 omission claims / 33 modules and 12
phantom claims / 18 modules; the fix removed 4 phantom claims and 8 phantom modules
outright and surfaced 4 more omission modules.

| | claims | module entries |
|---|---:|---:|
| OMISSION (higher confidence) | 19 | 37 |
| PHANTOM (lower confidence by design) | 8 | 10 |
| **total adjudications** | **27** | **47** |

## Method, and its limits

Check 41 is **definition-robust**: it reports only defects holding under all three
readings of Provides-To (D1 flow / D2 ownership / D3 blast), so the pending ruling
cannot invalidate a finding here. OMISSION means "in every definition, yet unclaimed";
PHANTOM means "in no definition, yet claimed".

Ground truth is the role map (`check_attribution_omissions.py --dump-rolemap`). I
cross-checked it with an independent probe — and **positive-controlled the probe first**
against a known edge (M14 reads `pm_climate_class`, declared in 45_climate) after an
earlier version of it silently returned "0 shared vars" for all eight phantom pairs
because it skipped the `declared_in` field, which is a string where the others are
lists. A uniform zero is the signature of a broken probe, not a finding.

**The standing limit that governs every PHANTOM row below**: the role map covers
`vm_`/`pm_`/`im_`/`fm_`/`pcm_`/`sm_` variables, **not GAMS sets**. A module that
provides only a set (M28 provides `ac` to 29/32) has no interface variable, so a real
coupling reads as a phantom. Phantoms are therefore *questions*, not defects.

---

## PHANTOM claims — 8 claims / 10 module entries

Every pair below was verified to have **no shared interface variable** in the role map.
That is necessary but not sufficient for "the doc is wrong": the coupling may be
set-based, conceptual, or routed through a third module.

| # | Doc | Claim | Phantom | Mechanism check | Verdict |
|---|---|---|---|---|---|
| P1 | `module_28.md:790` | downstream: 29,32,35,52 | **29, 32** | M28 declares **zero** interface vars; it provides the `ac` age-class set | **KEEP DOC — known limit 1.** Textbook set-based provision. The doc is right; the checker cannot see sets. |
| P2 | `module_32.md:1391` | receives from: 10,12,14,22,28,29,30,35,44,52,73 | **28** | Same `ac` set coupling, other direction | **KEEP DOC — known limit 1.** |
| P3 | `module_31.md:527` | provides to: 10,11,52,70 | **70** | M31 and M70 share **zero** identifiers of any interface prefix | **NEEDS MIKE.** No variable, and no set that I could identify. Either a conceptual link (pasture area ↔ livestock demand, mediated by M14/M70's `pm_past_mngmnt_factor`) or a genuinely stale claim. |
| P4 | `module_31.md:529` | depends on: 10,14,70 | **70** | As P3, reverse direction | **NEEDS MIKE.** Same pair; adjudicate P3 and P4 together. |
| P5 | `module_34.md:320` | depends on: 09 | **09** | M34 references only `fm_bii_coeff` and `fm_luh`, neither owned by M09 | **NEEDS MIKE.** Urban land plausibly depends on population drivers conceptually, but no GAMS edge exists. Note this claim's *whole* module list is the phantom — the row has no surviving entry. |
| P6 | `module_51.md:742` | provides to: 11,56 | **11** | M51 contains **no** `vm_cost*` variable at all | **LIKELY STALE — verify.** The natural mechanism (a nitrogen cost term flowing to the M11 cost aggregation) does not exist in M51's own code. |
| P7 | `module_52.md:1206` | provides to: 11,44 | **11, 44** | M52 contains **no** `vm_cost*` variable | **LIKELY STALE — verify.** Same shape as P6. Note this same line also carries the largest omission in the set (O13). |
| P8 | `module_52.md:1207` | depends on: 10,28,35 | **10** | M52 and M10 share **zero** interface identifiers | **NEEDS MIKE.** "Carbon depends on land" is intuitively obvious, which is exactly why it warrants checking rather than waving through — carbon reads land pools via `pcm_land`, which is declared by M10, so I would expect an edge and did not find one. **Re-derive this one before acting.** |

> ⚠️ **P8 caveat, stated rather than buried.** `pcm_land` is declared by 10_land and read
> by 13 modules including 59_som — so the M52↔M10 zero is surprising and may indicate a
> role-map gap rather than a doc error. Do not "fix" `module_52.md:1207` on the strength
> of this row.

---

## OMISSION claims — 19 claims / 37 module entries

Higher confidence by construction (present under *every* definition). I spot-verified 6
of the 19 against the role map; all 6 resolved to a concrete interface variable.

| # | Doc | Claim | Omitted | Verifying variable | Confidence |
|---|---|---|---|---|---|
| O1 | `module_13.md:438` | depends on: 09,10,12 | 22, 29 | `pm_avl_cropland_iso` (declared+populated 29, read 13) | **VERIFIED** |
| O2 | `module_15.md:19` | receives from: 09 | 56 | `vm_emission_costs` (declared+populated 56, read 11/15/56) | **VERIFIED** |
| O3 | `module_15.md:1539` | receives from: 09 | 56 | same as O2 — duplicate claim, same fix | **VERIFIED** |
| O4 | `module_20.md:737` | depends on: 16 | 17 | `vm_prod_reg` (declared 17, read by 20) | **VERIFIED** |
| O5 | `module_22.md:1366` | receives from: 10 | 29 | not individually verified | high |
| O6 | `module_31.md:529` | depends on: 10,14,70 | 22, 52 | not individually verified | high |
| O7 | `module_32.md:765` | provides to: 10,11,52,56,73 | 58 | not individually verified | high |
| O8 | `module_34.md:320` | depends on: 09 | 10 | not individually verified | high |
| O9 | `module_35.md:26` | receives from: 10,22,28,32,44 | 14, 52 | not individually verified | high |
| O10 | `module_35.md:966` | provides to: 10,11,22,32,52,56,73 | 59 | not individually verified | high |
| O11 | `module_36.md:577` | depends on: 09,38 | 57, 70 | see direction caveat below | high, **direction suspect** |
| O12 | `module_36.md:1024` | receives from: 09 | 38, 57, 70 | `pm_hourly_costs` is declared+populated by **36** and read by 70 | **DIRECTION SUSPECT** |
| O13 | `module_52.md:1206` | provides to: 11,44,56 | 14,29,30,31,32,35,59,73 | largest single omission (8 modules) | high |
| O14 | `module_52.md:1207` | depends on: 10,28,35 | 32, 56 | not individually verified | high |
| O15 | `module_56.md:1139` | depends on: 51,52,53,58 | 09, 10, 32 | ⚠️ **DO NOT EDIT** — this line is one of the 3 findings frozen pending the Provides-To ruling | **FROZEN** |
| O16 | `module_71.md:657` | depends on: 70 | 10, 17 | not individually verified | high |
| O17 | `module_73.md:1052` | provides to: 32 | 11, 62 | not individually verified | high |
| O18 | `module_73.md:1053` | depends on: 09 | 52 | `im_vol_conv` (declared+populated 52, read 52/73) | **VERIFIED** |
| O19 | `module_80.md:1070` | depends on: 11 | 10 | `vm_landdiff` (declared+populated 10, read 10/80) | **VERIFIED** |

> ⚠️ **O11/O12 direction caveat.** The verifying variable for the M36↔M70 pair is
> `pm_hourly_costs`, which M36 **declares and populates** and M70 **reads**. That is
> M36 *providing to* M70. Both claims are phrased as "depends on" / "receives from", so
> adding 70 there may record the edge **backwards**. Check 41 tests set membership, not
> direction — Check 36 (`check_dependent_direction`) is the direction instrument, and it
> currently reports 0 findings with 19 pairs skipped. **Adjudicate direction before
> adding these.**

---

## Recommended handling

1. **P1, P2 — close as KEEP DOC.** Set-based provision, the checker's documented blind
   spot. Consider recording them in `audit/advisory_allowlist.json` with the limit class,
   so they stop consuming attention every run. (An allowlist hook for Check 41 was in
   scope for tonight and is **not built** — see the run's STATUS block.)
2. **O1–O4, O18, O19 — safe to apply.** Verified to a named variable.
3. **O15 — do not touch.** Frozen pending the Provides-To ruling.
4. **O11, O12 — resolve direction first.**
5. **P8 — re-derive before acting.** The surprising zero may be a role-map gap.
6. **P3–P7 — need a human call** on whether the claim is conceptual or stale.

## Provenance

Role map: `scripts/check_attribution_omissions.py --dump-rolemap`, post-fix `179ddeb`.
Findings: `scripts/check_module_set_claims.py`, run through its real entry point.
Nothing in this table was auto-applied. Nothing was pushed.
