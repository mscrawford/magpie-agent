# Module 32 (Forestry) — Notes

**Created 2026-07-14** during the `/sync` to MAgPIE develop `0d7ebeb90`.

---

## ⚠️ Warnings & Common Mistakes

### Silent zero: `affexp` / `ndcdelay` vs the pinned input revision

**If you select `c32_aff_policy = ndcdelay` or `affexp` on develop today, you very likely get NO afforestation policy at all — silently, with no GAMS error.** Check the input file before trusting a run.

**Why this can happen.** The afforestation-policy switch has **no code branch whatsoever**. The entire policy selection is one table lookup:

```gams
p32_aff_pol(t,j) = round(f32_aff_pol(t,j,"%c32_aff_policy%"),6);
```
(`modules/32_forestry/dynamic_may24/preloop.gms:182`)

So a policy's whole substance is a **column** of the downloaded input file `npi_ndc_aff_pol.cs3` (`input.gms:73`; produced by `calcOutput("NpiNdcAffPol")`, so it is **not in git**). Declaring a new member of `pol32` in `sets.gms` does *not* create any data. If the `.cs3` header has no column for the selected policy, GAMS leaves `f32_aff_pol` at its default of 0 for that member — no domain violation, no warning — and `p32_aff_pol` is zero everywhere.

**What was actually verified (2026-07-14, develop `0d7ebeb90`):**

| Fact | Where |
|---|---|
| `pol32` = `/ none, npi, ndc, affexp, ndcdelay /` | `dynamic_may24/sets.gms:19-20` |
| Zero code branches on `ndcdelay` anywhere in `*.gms` | only the set member, the `input.gms:10` options comment, and the `f32_aff_pol` table description mention it |
| The pinned input's `.cs3` header is `dummy,dummy,none,npi,ndc` | `modules/32_forestry/input/npi_ndc_aff_pol.cs3` — **3 policy columns**; `affexp` and `ndcdelay` appear **0 times** in all 6405 lines |
| That `.cs3` is `rev4.131` — the revision develop pins | `input/info.txt` vs `cfg$input` cellular in `config/default.cfg` |
| Neither the `affexp` commit (`a54cd02c6`, 2026-05-27) nor the `ndcdelay` commit (`58bde5788`, 2026-07-02) bumped `cfg$input` | `git log -- config/default.cfg` |

So both `affexp` and `ndcdelay` are **selectable but unfed** under the input revision develop currently pins. The features are presumably fine; the *input pin has not caught up* — the preprocessing (`mrmagpie` `NpiNdcAffPol`) has to be re-run and a new revision published and pinned before either policy does anything.

**Not verified:** this is a code + input-file trace, **not** an empirical run. If you need certainty, run with `c32_aff_policy = ndcdelay` and check `p32_aff_pol` in the GDX — it should be identically zero.

**How to check before any run using a non-default `c32_aff_policy`:**
```bash
head -5 modules/32_forestry/input/npi_ndc_aff_pol.cs3 | grep -v '^\*'   # the header row lists the columns you actually have
```
If your policy isn't in that header, the run will do nothing and tell you nothing.

**Generalize this.** The same shape appears wherever a switch indexes straight into a file parameter with no code branch — `c22_protect_scenario` into `f22_consv_prio` is the same pattern (`modules/22_land_conservation/area_based_apr22/preloop.gms:42`), and the 2026-06 LandMark options landed the same way. **A new set member is a promise; the input column is the delivery.** When a sync adds a set member, check whether the data exists.

---

## 💡 Lessons Learned

- 2026-07-14: `c32_aff_policy` is a pure data lookup (`preloop.gms:182`) with no code branch — so a policy is only as real as its column in `npi_ndc_aff_pol.cs3`. Adding a `pol32` member without a matching input revision produces a silent all-zero policy. Found during the sync of `58bde5788` (ndcdelay / PRISMA). (Source: session experience.)
- 2026-07-14: When a develop sync adds a member to a set that indexes a **downloaded** input table, always check the shipped file's header before documenting the option as usable. The GAMS "missing column reads as 0" behaviour makes this class of gap invisible to both the compiler and the validator. (Source: session experience.)

---

## See also

- `module_32.md` — primary documentation (§9.2 Afforestation Policy)
- `module_22.md` — same switch-into-downloaded-table pattern (`c22_protect_scenario` → `f22_consv_prio`)
- `module_56_notes.md` — C-price-induced afforestation is a *different*, reward-driven channel (`vm_reward_cdr_aff`), independent of `c32_aff_policy`
- `agent/helpers/debugging_infeasibility.md` — for runs that fail loudly; this note is about a run that fails **quietly**
