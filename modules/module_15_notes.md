# Module 15 (Food Demand) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session

---

## ⚠️ Warnings

1. **s15_exo_diet default is 0**: This means ALL EAT-Lancet diet settings (s15_exo_waste, s15_exo_*_substitution, etc.) are SILENTLY IGNORED unless you set `s15_exo_diet=1`. This is the #1 mistake in diet scenario setup.

2. **BMI equations use cumulative normal distributions**: The q15_bmi_shr equations compute population shares in BMI categories using `p15_bmi_shr_regr` regression parameters. These are NOT simple linear relationships — unexpected BMI results may be due to nonlinear threshold effects.

3. **18 equations fully documented** (validated 2026-03-06): All equations in `anthro_iso_jun22` realization verified against GAMS code.

## 💡 Tips

- For EAT-Lancet scenarios: set `s15_exo_diet=1`, then configure `s15_exo_waste`, `s15_exo_*_substitution` parameters.
- Don't combine EAT-Lancet diet switching (`s15_exo_diet=1`) with food substitution scalars — risk of double-counting.
- See `agent/helpers/scenario_diet_change.md` for complete step-by-step guide.

## 📝 Lessons from Usage

- Realization path is `anthro_iso_jun22` (not older `anthropometrics_jan18`)
