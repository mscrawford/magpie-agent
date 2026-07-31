# Interface role definitions — what "Provides To" and "Depends On" mean

**Decided** 2026-07-20 (Mike: *"Best have clear definitions"*, delegating after
*"the exact definition should be consistent. You decide"*). This file is the SSOT
for the terms. If a doc, a checker, or an audit uses these words, it means what
is written here.

---

## The actual defect: three questions, two column headers

`core_docs/Module_Dependencies.md` §1.2 has columns `Provides To` / `Depends On`,
and the corpus has been using them for three different questions at once. That —
not arithmetic drift — is why the layers disagree.

The three questions, each legitimate:

| # | Question | Name it |
|---|---|---|
| D1 | Whose values flow into whom? | **data flow** |
| D2 | Who owns the interface a module reads? | **interface ownership** |
| D3 | What could break if I change M? | **coupling / blast radius** |

## The primitives

For each interface symbol `v`, from the role map
(`scripts/check_attribution_omissions.py --dump-rolemap`):

- **`owner(v)`** — the module whose `declarations.gms` declares it. Unique, or
  flagged ambiguous. **Total**: every symbol has one.
- **`writers(v)`** — modules that DETERMINE ITS VALUE: an assignment, an equation
  whose LHS lead token is `v`, or a `.fx` fix. Bound/level/scale writes
  (`.lo`/`.up`/`.l`/`.scale`) are excluded — see B4, commit `f7d4e10`.
- **`readers(v)`** — modules that reference `v` without writing it.

## The definitions

```
D1  ProvidesTo_flow(M)   = { X != M : ∃v, M ∈ writers(v) ∧ X ∈ readers(v) }
D2  ProvidesTo_owner(M)  = { X != M : ∃v, owner(v) = M ∧ X ∈ readers(v) }
D3  ProvidesTo_blast(M)  = { X != M : ∃v, M ∈ writers(v) ∪ {owner(v)} ∧ X ∈ readers(v) }
```

`DependsOn` is the mirror of each, swapping the roles of `M` and `X`.

## ⚠️ THE D2 DECISION BELOW IS WRONG — REOPENED 2026-07-20, SAME DAY

**D2 has a semantic hole, found while applying it to the docs and verified in
code.** It is preserved below rather than deleted, because the reasoning that
produced it shows exactly how a confident wrong definition gets adopted.

**The case that breaks it.** `vm_emissions_reg` is DECLARED by M56, POPULATED by
{51, 52, 53, 58}, and READ by {56, 57}. M56's own `q56_emission_costs` sums it.
So M56's cost equation genuinely **depends on** 51/53/58 filling their slices —
but D2's `DependsOn(M)` only looks at the OWNER of symbols M reads, and here M56
owns the symbol itself. **The contributor -> declarer edge vanishes.**

This matters concretely: `module_56.md:1139` says
`**Depends on**: Modules 52 (carbon stocks), 53 (methane), 51 (N₂O), 58 (peatland)`,
which is **correct**, and D2 would have replaced it with {09, 10, 12, 32}. That
is a right claim being overwritten by a mechanically-derived wrong one — the
precise failure the R55/R56 arc exists to prevent. The edit was reverted before
being committed.

**Reason 5 below ("best fit on the evidence: 5 of 10 rows") was the bad
criterion** and is what tipped the choice. Fitting a table that is itself
internally inconsistent is not evidence of correctness; it selects for agreeing
with whatever produced the existing numbers.

**D3 is the only candidate without a known hole** — it captures all three real
edge types in MAgPIE's shared-variable idiom:

| Edge | Meaning | D1 | D2 | D3 |
|---|---|---|---|---|
| owner -> readers | who owns the interface you read | ✗ | ✓ | ✓ |
| writer -> readers | whose slice value flows to you | ✓ | ✗ | ✓ |
| writer -> owner | who fills the variable you aggregate | ✗ | ✗ | ✓ |

D3 numbers for the §1.2 rows (Total / Provides / Depends): M11 28/1/27,
M10 23/18/5, M56 18/5/13, M32 28/17/11, M30 26/17/9, M70 15/7/8, M17 19/12/7,
M09 14/14/0, M29 24/15/9, M35 26/17/9.

**D3's own weakness, stated rather than hidden:** it is coarse. Because every
land module populates slices of shared variables, M32/M30/M35/M29 all land in
24-28 and the metric stops discriminating. A single integer is compressing a
multi-relation graph, and no compression is free.

## RULED 2026-07-31 (Mike): report TWO columns — **Owns** and **Reaches**

`Owns` = D2 (owner -> readers). `Reaches` = the D3 union. The single `Total` goes
away: it cannot hold across two definitions, so the `Total = ProvidesTo + DependsOn`
identity is retired with it.

**Why two, rather than picking one.** Neither definition dominates, and the
measurement says so. D2 discriminates about twice as well among the land modules
(spread 5-11 versus D3's 15-17) — but that discrimination is partly an artifact of
ignoring the edge type that dominates MAgPIE's idiom. The decisive case: **M31
declares exactly one interface variable (`vm_cost_prod_past`) but writes slices of
`vm_land`, `vm_carbon_stock`, `vm_prod`, `vm_bv`, which 21 modules read.** §1.2 exists
to answer *"if I touch this module, what breaks?"* and feeds
`cross_module/modification_safety_guide.md`; for M31, D2 answers **1**, which is
dangerously wrong. D3 answers 21 and is right. Reporting both keeps the exact,
anchored, discriminating number AND the blast radius, and the gap between them is
itself the useful signal.

**`writers` was fixed FIRST, per the same ruling** — see the balance-equation section
below and commit `d000be1`. POPULATE now credits a `vm_` symbol summed on an equation
LHS. Measured: POPULATE edges 150 -> 161, READ 423 -> 420 (3 reclassifications, not
losses). So the numbers below are computed against the corrected map, not the old one.

**Recomputed §1.2 rows** (positive control: M10 Owns = 18, matching the independent
hand-derivation at `modules/module_10.md:793`):

| Module | Owns | Reaches | gap |
|---|---:|---:|---:|
| M11 costs | 1 | 1 | 0 |
| M10 land | 18 | 18 | 0 |
| M56 ghg_policy | 5 | 5 | 0 |
| M32 forestry | 6 | 17 | +11 |
| M30 croparea | 10 | 16 | +6 |
| M70 livestock | 7 | 7 | 0 |
| M17 production | 12 | 12 | 0 |
| M09 drivers | 14 | 14 | 0 |
| M29 cropland | 7 | 15 | +8 |
| M35 natveg | 5 | 18 | +13 |

The gap column separates two kinds of module cleanly: gap-zero modules own what they
provide, while the large-gap ones (M35, M32, M29, M30, and M31 at +20) are land modules
whose blast radius comes entirely from writing slices of variables they do not own.

**DONE 2026-07-31 — the doc pass landed.** Written into `core_docs/Module_Dependencies.md`
§ 1.2, `cross_module/modification_safety_guide.md` Appendix A, and seven module docs. The
three frozen dependent-count findings (`module_56.md`, `module_17.md`) are resolved, and
`module_29.md`'s standing R58 caveat — "the cited source does not say that", held for
human adjudication — is closed with doc and code agreeing.

**The numbers now have a persisted source.** `audit/tools/compute_module_centrality.py`
regenerates the table from `build_role_map()`, the same ground truth the validator uses.
Written because item R6 forbids citing a figure that has no artifact behind it, and the
ruling's own table had been computed in a throwaway heredoc. Regenerate; do not hand-edit.

> **The surface measurement in the previous version of this section was WRONG, in the
> direction that matters.** It claimed **"only 2"** module lines carried a hard number. The
> real count is **seven module docs** — 09, 11, 17, 29, 30, 32, 35 — three of which restate
> the rank a second time in a risk-justification line. A 3.5x undercount of the surface, and
> it would have shipped a corpus where half the module docs contradicted the core table.

**Two findings that only appeared once the numbers were computed:**

1. **Retiring `Total` also retired the row SELECTION.** §1.2 was the top 10 *by `Total`*, so
   the membership had no surviving justification. Under `Reaches` the old list was wrong in
   both directions: it omitted `31_past`, which ranks **first** at 21, and `34_urban` at 16,
   while seating `11_costs` at rank 1 on a reach of 1. Ruled 2026-07-31 (Mike): re-rank by
   `Reaches` and fix membership; `11_costs` becomes a footnote. Ranks 10-12 tie at 11 and are
   all shown, because cutting two of three tied rows misreports coverage.

2. **The M10 positive control is BLIND to the distinction it was cited for.** This section
   originally offered "M10 Owns = 18, matching the hand-derivation at `modules/module_10.md:793`"
   as the control licensing the ruling. M10 is a **gap-zero** module, so D2 and D3 return the
   same answer for it: the mutation swapping `Owns` to read D3 was run, and it **survived**.
   The anchor validates the role map; it never validated the choice of definition. The
   self-test now also pins `31_past` (Owns 1 / Reaches 21, gap +20), independently grounded in
   `../modules/31_past/*/declarations.gms` declaring exactly one interface variable, plus an
   assertion that the two definitions have not collapsed. Both mutation directions now die.

**A third, independent corroboration of `Reaches`** surfaced during the pass: the R58
hand-derivation in `modules/module_29.md` enumerated 14 downstream modules for M29. Computed
`Reaches` is 15 and `Owns` is 7 — so that hand-derivation was reaching for the union
definition all along, and its one omission (M58, which reads a `vm_land` slice M29 writes) is
explained rather than hand-waved.

---

## SUPERSEDED — DECISION: §1.2 and the per-module docs report **D2 (interface ownership)**

Reasons, in order of weight:

1. **It is what the table is FOR.** §1.2 is "Module Centrality Rankings" and feeds
   `cross_module/modification_safety_guide.md`. The question a reader brings is
   *"if I touch this module, what breaks?"* — ownership, not value flow.
2. **It is total.** Every symbol has an owner, so D2 is defined for every module.
   D1 is not: it is silent wherever a variable is determined jointly by
   constraints rather than assigned.
3. **It already agrees with the layer that was hand-verified.** D2 gives M10 = 18,
   which is exactly what `modules/module_10.md:793` independently derived and
   enumerated by module number.
4. **It is what the checker already computes**, so adopting it makes
   `check_dependent_counts` and the docs answer the same question for the first
   time.
5. **It fits the doc corpus best on the evidence**: 5 of 10 §1.2 rows, versus 2
   for D1 and 3 for D3.

### On the "provides = populates" intuition

Mike's instinct — *provides to means to populate* — is **correct about D1** and is
why D1 is defined and named here rather than discarded. It is not what §1.2
should report, because under D1 **M10 does not provide `vm_land`**: the
land-using modules (29, 31, 32, 34, 35) compute their own slices, and M10 owns
only the balance identity. True as data flow, useless as centrality.

Keep both. Use the right one, and say which.

## Numbers under each definition (top-10 §1.2 rows, 2026-07-20)

| Module | doc as written | D1 flow | **D2 owner** | D3 blast |
|---|---|---|---|---|
| 11_costs | 1 | 1 | **1** | 1 |
| 10_land | 15 | 16 | **18** | 18 |
| 56_ghg_policy | 13 | 5 | **5** | 5 |
| 32_forestry | 5 | 16 | **6** | 17 |
| 30_croparea | 9 | 17 | **9** | 17 |
| 70_livestock | 7 | 6 | **7** | 7 |
| 17_production | 13 | 8 | **12** | 12 |
| 09_drivers | 14 | 14 | **14** | 14 |
| 29_cropland | 6 | 15 | **7** | 15 |
| 35_natveg | 5 | 16 | **5** | 17 |

Rows matching the doc: D1 = 2, **D2 = 5**, D3 = 3.

## What this settles, and what it does not

**Settled.** The long-running disputes resolve mechanically once the definition
is fixed:

- `module_56.md:1138`/`:1150` "13 modules" -> D2 truth **5**. The 13 counted
  modules that POPULATE M56's declared variables as recipients; they are
  contributors, so the arrow was reversed.
- `module_17.md:899` "13 downstream" -> D2 truth **12**.
- `core_docs/Module_Dependencies.md:32` M10 = 15 -> D2 truth **18** (and Total
  17 -> 20, since the table's `Total = ProvidesTo + DependsOn` identity holds on
  all 10 rows).

**NOT done here, deliberately.** No number has been written into any doc. Editing
them is a corpus-wide pass touching §1.2, several `module_NN.md` centrality
lines, and the Total column, and it deserves its own reviewed change with the
before/after diff visible — not a footnote to a definitions file.

**Still open — the balance-equation blind spot (smaller than first reported).**
`writers(v)` misses a variable constrained by a balance-style equation, because
the LHS lead token is `sum`, not the variable: M10's
`sum(land, vm_land(j2,land)) =e= ...` does not register. **Correction on record:**
this was first escalated as "`vm_land` now has no populator at all" — that was
wrong. `writers(vm_land) = {29, 31, 32, 34, 35}`; the slice populators are
detected fine, and only M10 is absent. Under D2 this does not affect §1.2 at all,
since D2 does not consult `writers`. It only matters if D1 is ever reported.
**PRICED, rather than parked** (5 min, per `feedback_price_a_deferred_lead`).
26 (var, module) pairs sit on an equation LHS without being the lead token. Read
individually, they split cleanly:

- **~19 are genuine constraint relationships** — an aggregation or balance
  equation where the variable really is being determined:
  `sum(land, vm_land(j2,land))` (M10), `sum(supreg(h2,i2), vm_prod_reg(i2,kall))`
  (M21), `sum(kcr, vm_area(j2,kcr,"irrigated"))` (M41),
  `sum(wat_dem, vm_watdem(wat_dem,j2))` (M43).
- **~7 are reads, not writes** — a parameter used as a coefficient inside the
  LHS expression: `im_demography` (M15), `pm_labor_prod` and
  `pm_productivity_gain_from_wages` (M38), `fm_attributes` (M20). Classifying
  these as writes would be a NEW error, so a naive "also credit anything on the
  LHS" fix would be worse than the gap.

**Consequence: under D2 this needs no action at all.** D2 never consults
`writers`, so none of the 26 affects §1.2, the per-module centrality lines, or
`check_dependent_counts`. The gap becomes live only if D1 is ever reported, and
at that point the fix is "credit a variable summed on the LHS, but not one
appearing only as a factor in a product" — which the split above already
specifies. Deferred with a known price, not an unknown one.
