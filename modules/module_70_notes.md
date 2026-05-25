# Module 70 (Livestock) — Notes

**Backfilled 2026-05-25** from `audit/validation_rounds.json` R22 findings (R6 Cluster C2).

---

## ⚠️ Warnings & Common Mistakes

### `vm_costs_additional_mon` is in M71, NOT M70

Common attribution error: `vm_costs_additional_mon` (1-dimensional cost variable) is declared in **Module 71 (livestock disaggregation)**, not M70. Specifically in `modules/71_disagg_lvst/foragebased_jul23/declarations.gms`. M70 reads it.

"Additional mon" means **additional monogastric** (a calibration adjustment for pig/poultry feed), NOT "monitoring" or "month".

The calibration parameter `s71_punish_additional_mon = 15000` is the punishment cost. The penalty equation is `q71_punishment_mon` in the same `foragebased_jul23` realization.

### `foragebased` realization naming

The default M71 livestock-disaggregation realization is `foragebased_jul23` (not `foragebased_aug18` — that was the prior version). `module_70.md:712` and `module_11.md:496` previously cited the stale `_aug18` path; fixed in R22.

When citing M71 paths, double-check the realization tag against `ls ../modules/71_disagg_lvst/` to confirm you're not referencing the old realization.

---

## 💡 Lessons Learned

- 2026-05-25: Always distinguish M70 (livestock) from M71 (livestock disaggregation). M70 declares aggregate livestock cost variables; M71 declares disaggregated (monogastric vs ruminant) cost variables. (Source: R22 Q2 audit.)
- 2026-05-25: When citing realization paths for M70/M71 work, run `ls ../modules/70_livestock/ ../modules/71_disagg_lvst/` first to confirm current names. The `_aug18` → `_jul23` rename for M71's foragebased realization was a common stale-citation source.

---

## 🧪 Real-World Examples

- **Livestock feed basket scenarios**: see `agent/helpers/scenario_diet_change.md` for diet-side scenario controls; M70 implements the supply side.

---

## See also

- `module_70.md` — primary documentation (livestock production)
- `module_71.md` — disaggregation (monogastric vs ruminant)
- `agent/helpers/scenario_diet_change.md` — demand-side diet scenarios
