# Helper: Debugging GAMS Compile & Execution Errors

**Auto-load triggers**: "compilation error", "won't compile", "compile error", "Error 141", "Error 149", "Error 170", "Error 171", "Error 257", "Error 455", "domain violation", "uncontrolled set", "FUNC SINGULAR", "division by zero", "bad delimiter", "execution error", "Exec Error", "hundreds of errors", "$170", "$171"
**Lessons count**: 2 entries

> This helper is for **GAMS errors** (the model does not compile, or aborts during
> execution), NOT for optimizer infeasibility. If the model compiles, executes, and
> then a `solve` returns an infeasible `modelstat`, use `debugging_infeasibility.md`.
> But first read "Real infeasibility vs skipped solve" below: a MAgPIE run that aborts
> with "... became infeasible during initialisation" is frequently a GAMS *execution*
> error, not a real infeasibility.

---

## Quick Reference

### GAMS errors cascade — always find the FIRST (root) error

A failed run often reports **hundreds** of errors. They are listed in `full.lst` in
**source order, not causal order**. Almost all of them cascade from 1-2 root errors
near the top. Do not start from the last error or the error count.

**Find the root fast:**

1. **Search `full.lst` for `$`.** GAMS underlines the offending token in the echoed
   source by placing `$<code>` in a marker line directly beneath it, e.g.
   ```
   684290  dummy,dummy,dummy,tece,maiz,...
   ****        $170  $170  $170 $1   $1 ...
   ```
   The **first** `$`-marker in the file is the root error. Every `****` marker line
   and every column marker uses `$`, so a plain search for `$` walks you to them in
   order.

2. **Tally the error codes** to see the shape of the failure:
   ```bash
   grep -oE '^\*\*\*\* +[0-9]{3}  ' full.lst | sort | uniq -c | sort -rn
   ```

3. **Read the context of the first marker only.** Fix that; re-run. The cascade
   usually disappears wholesale.

### Codes that are almost always DOWNSTREAM noise (do not start here)

| Code | Meaning | Why it is usually a symptom |
|---|---|---|
| `141` | Symbol declared but no values assigned | The assignment/solve that would have populated it was aborted by an earlier error |
| `257` | Solve statement not checked because of previous errors | A prior compile/exec error blocked the solve |

Seeing 300-700 of these with a handful of `170`/`171`/`149`/`455` at the top means:
fix the handful, ignore the hundreds.

### Common root codes and their typical cause in MAgPIE

| Code | Meaning | Typical MAgPIE cause |
|---|---|---|
| `170` | Domain violation for element | A data record / set element not in the declared domain (e.g. a year in the data file not in `t_past`) |
| `171` | Domain violation for set | A symbol indexed by a set that is not a subset of its declared domain (e.g. a `t_past`-declared parameter used over `t_all`) |
| `149` | Uncontrolled set entered as constant | A non-singleton set (often `ct`) used as a bare index in an equation without `sum(<set>, ...)` |
| `455` | Bad or missing delimiter while reading delimited data records | A malformed `.cs*` input file (e.g. a comment line that does not start with `*`, so `$ondelim` mis-parses header vs data) |
| `1` | Real number expected | Text (e.g. a column label) appears where GAMS expected a numeric value, usually because header/data rows got misaligned |

---

## Compile errors vs execution errors vs infeasibility

Three distinct failure stages, three different places to look:

1. **Compile errors** — reported during `--- Starting compilation`. Marked with `****`
   and `$<code>` in `full.lst`. The job stops with `*** Status: Compilation error(s)`
   and no solve happens. Diagnose with the "find the root" steps above.

2. **Execution errors** — reported during `--- Starting execution`. Marked with
   `**** Exec Error at line N` in `full.log`/`full.lst`. Examples: `log: FUNC SINGULAR: x = 0`
   (log of a non-positive number), `division by zero`. These accumulate an `EXECERROR`
   count. **A pending `EXECERROR > 0` makes GAMS SKIP subsequent solves** (see below).

3. **Solver infeasibility** — the model compiled and executed, a `solve` ran, and the
   returned `modelstat` is infeasible. This is the only case that belongs in
   `debugging_infeasibility.md`.

### Real infeasibility vs skipped solve (important MAgPIE trap)

MAgPIE may `abort` with a message like
`"Food Demand Model became infeasible already during initialisation run. Stop run."`
That message is **misleading**. Check `full.lst`/`full.log` for:

```
**** SOLVE from line <N> SKIPPED, EXECERROR = <k>
```

If present, the solve was **never run** — `k` execution errors (log(0), div-by-zero,
etc.) fired in preloop/presolve *before* the solve, so GAMS skipped it and the model's
`modelstat` stayed `NA`, which the abort check reports as "infeasible". The fix is to
hunt the execution errors, **not** to relax constraints, inspect marginals, or touch
land/water balances. See `debugging_infeasibility.md` "Step 0".

---

## Pitfalls

### Execution-error line numbers do not map to physical `full.gms` lines

The line number in `**** Exec Error at line N` (and in `full.log`) often does **not**
correspond to physical line `N` of `full.gms` — reading that line frequently lands you
on a comment block or the wrong module. Do not trust it for attribution. Instead:

- Read the **actual statement echoed in `full.lst`** next to the error, or
- Inspect the values of the symbols involved with `gdxdump`:
  ```bash
  gdxdump fulldata.gdx symb=<param> format=csv | head
  ```
  Finding the zero / `Undf` / missing-year entry that triggered the `log`/division is
  the fastest way to attribute the error to the right module. (`fulldata.gdx` is
  written by `execute_unload` even on an aborted run.)

---

## Module Cross-References

| Topic | Read |
|---|---|
| Optimizer infeasibility (real) | `agent/helpers/debugging_infeasibility.md` |
| `ct` / `sum(ct, ...)` idiom, time sets, `t_past` | `reference/GAMS_MAgPIE_Patterns.md` §4 |
| Reading model outputs / gdx | `agent/helpers/interpreting_outputs.md` |
| GAMS error-message reference | `reference/GAMS_Fundamentals.md`, `reference/GAMS_Best_Practices.md` |

---

## Lessons Learned
<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
- 2026-07-14: GAMS errors cascade in source order, not causal order. A run with hundreds of `141`/`257` errors almost always stems from 1-2 root `170`/`171`/`149`/`455` errors earlier in `full.lst`. Search the listing for `$` to jump to the first error marker (GAMS underlines the offending token with `$<code>`); fix that one and re-run before touching anything else. `141` (symbol without values) and `257` (solve skipped) are downstream noise. (source: session experience — fallow branch, multiple runs collapsed 350-747 errors to a single root each time)
- 2026-07-14: `**** Exec Error at line N` line numbers do NOT reliably map to physical `full.gms` lines — attribution by line number sent debugging to the wrong module (52) before the actual culprit (36) was found via the echoed statement + `gdxdump fulldata.gdx symb=<param>`. Use the listing's echoed statement and the gdx values to attribute execution errors, not the reported line number. (source: session experience)
