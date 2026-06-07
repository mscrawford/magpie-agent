# Round 49 Verification — nitrogen_food_balance.md

Verifier: adversarial (Opus). Ground truth: /tmp/magpie_develop_ro (develop worktree).
Target doc: cross_module/nitrogen_food_balance.md

---

## nfb-B1 — Stale/imprecise file:line citation at nfb:183

**Verdict: UPHELD** (class: realization_structure; citation_ok: true)

### Doc claim (nfb:183)
> **Source**: Module 21, `modules/21_trade/selfsuff_reduced/equations.gms:10-25`

This closes the "Regional Balance" subsection (nfb:178) whose named equation is `q21_trade_reg`.

### STEP A — Mechanical citation check

File existence + range:
```
$ test -f /tmp/magpie_develop_ro/modules/21_trade/selfsuff_reduced/equations.gms
EXISTS
$ wc -l .../equations.gms
78 lines  -> all cited lines (10-25, 12-14, 31-35, 39-42, 12-42) IN RANGE
```

Exact-line token reads (`sed -n 'Np'`):
```
L10:  *' This means that production can be freely allocated globally based on comparative advantages.   [COMMENT]
L12:   q21_trade_glo(k_trade)..                                                                          [eq def]
L14:    sum(i2, vm_supply(i2,k_trade)) + sum(ct,f21_trade_balanceflow(ct,k_trade));                      [eq body end]
L18:   q21_notrade(h2,k_notrade)..                                                                       [eq def]
L25:  *' [@schmitz_trading_2012]. If the trade balance reduction equals 1, all demand enters ...        [COMMENT]
L31:   q21_trade_reg(h2,k_trade)..                                                                       [eq def]
L35:    - v21_import_for_feasibility(h2,k_trade);                                                        [eq body end]
L39:   q21_trade_reg_up(h2,k_trade) ..                                                                   [eq def]
L42:    / sum(ct,i21_trade_bal_reduction(ct,k_trade));                                                   [eq body end]
```

All file_evidence + proposed_fix citations resolve to the claimed tokens. citation_ok = TRUE.

### STEP B — Classify
`realization_structure`: the claim is about which equations the **selfsuff_reduced** realization defines and at what line ranges (equation presence + line-range structure within one named realization's file). Verified against THAT realization's actual file, never the sibling `selfsuff_reduced_bilateral22` (which also exists in the dir: `ls` shows `exo/`, `selfsuff_reduced/`, `selfsuff_reduced_bilateral22/`).

### STEP C — Adjudicate (citation_ok=true)

Full equation-definition map of the realization (grep `q21_[a-z_]+(` — positive control, all q21_ eqs present, search works in dir):
```
12: q21_trade_glo(k_trade)..
18: q21_notrade(h2,k_notrade)..
31: q21_trade_reg(h2,k_trade)..
39: q21_trade_reg_up(h2,k_trade) ..
47: q21_excess_dem(k_trade)..
56: q21_excess_supply(h2,k_trade)..
62: q21_cost_trade_tariff(h2)..
69: q21_cost_trade_margin(h2)..
76: q21_cost_trade_feasibility(h2)..
```

Absence confirmation (second method) — `q21_trade_reg` is NOT in the doc-cited range 10-25:
```
$ sed -n '10,25p' equations.gms | grep -n 'q21_trade_reg'
ABSENT in 10-25 (confirmed via grep no-match)
```

The doc's "Regional Balance" subsection is named after `q21_trade_reg`, but its cited Source range `10-25` ends at line 25 (a comment) while `q21_trade_reg` begins at line 31 — OUTSIDE the range. Lines 10-25 hold only `q21_trade_glo` (12-14) and `q21_notrade` (18-19, the non-tradable equation, not a regional self-sufficiency band). The auditor's reality_in_code reproduces exactly.

The proposed fix's citations are all mechanically correct:
- q21_trade_glo at :12-14 ✓ (already cited correctly at nfb:175)
- q21_trade_reg at :31-35 ✓
- q21_trade_reg_up at :39-42 ✓

### Recommendation to fixer
UPHELD. Apply the proposed fix. The broader-range option `equations.gms:12-42` is the cleaner choice for the "Regional Balance" subsection because the production-band equations the subsection is actually about are `q21_trade_reg` (31-35, lower bound) and `q21_trade_reg_up` (39-42, upper bound); spanning 12-42 captures the global constraint plus both regional band equations. Either the explicit `:12-14 and :31-35` form or the `:12-42` span is correct. (Minor severity: prose mechanism is right; only the line range is imprecise.)
