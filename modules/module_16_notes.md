# Module 16 (Demand) — User Notes & Warnings

**Last updated**: 2026-03-06
**Source**: Deep validation session

---

## ⚠️ Warnings

1. **Module 16 aggregates demand from multiple sources**: Food (Module 15), feed (Module 70), bioenergy (Module 60), material (Module 62), and processing (Module 20). Changes to any of these modules propagate through Module 16.

2. **Trade interaction**: Module 16 demand feeds into Module 21 (trade), which balances global supply=demand. If demand is set unrealistically high, the trade module or food balance may become infeasible.

## 💡 Tips

- To understand why demand changed, trace it back to the source module (15, 60, 62, 70).
- Module 16 itself has relatively few equations — most of the complexity is in the modules it aggregates.
