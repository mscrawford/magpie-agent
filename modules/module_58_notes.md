# Module 58 (Peatland) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session + comprehensive scalar analysis

---

## ⚠️ Critical Warnings

1. **💥 GUARANTEED INFEASIBILITY**: Setting `s58_rewetting_switch=0` while `s58_rewetting_exo=1` creates a guaranteed infeasibility — the upper bound is 0 but the constraint demands positive rewetted area.

2. **💥 GUARANTEED INFEASIBILITY**: Setting `s58_annual_rewetting_limit=0` while any exogenous rewetting is active creates the same contradiction.

3. **⚠️ LIKELY INFEASIBLE**: Setting `s58_rewet_exo_target_value ≥ 1.0` with default rate limit (0.02/yr) — max achievable is ~50% by 2050 from 2025 (5 timesteps × 10%/timestep).

4. **⚠️ SILENT BUG**: Setting `s58_fix_peatland` to a year NOT in MAgPIE's timestep set (e.g., 2019) means `p58_peatland_ref` is never populated → all rewetting targets are silently zeroed.

5. **17 scalars total** — all in `modules/58_peatland/v2/input.gms:8-26`.

## 💡 Tips

- All 5 cost parameters are safe to modify (pure cost coefficients, no feasibility impact).
- `s58_balance_penalty` default is $1M — setting to 0 allows solver to exploit free slack.
- `s58_rewetting_exo_noselect` has NO practical effect by default — policy_countries58 includes all 249 ISO countries.
