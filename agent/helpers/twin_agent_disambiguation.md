# Twin-agent disambiguation

**Auto-load triggers**: "flywheel", "round N", "validation round", "verification round", "validation_rounds.json", "preproc agent", "which agent", "twin agent"

**Hoisted from AGENT.md 2026-07-31** to keep the always-loaded router under its size
threshold. The *trigger* stays in AGENT.md — the ambiguous-term list and the instruction
to ASK — because a rule that only loads after you have already misrouted is worthless.
What lives here is the detail you need once the trigger has fired.

---

Two independent agents share this workspace, each with its own flywheel and
validation_rounds.json (magpie-agent: `audit/validation_rounds.json`; preproc-agent:
`feedback/validation_rounds.json`). This file's parent — AGENT.md and its deployed
copies — auto-loads; the preproc-agent's `PREPROC_AGENT.md` does **NOT**. Counter that
asymmetric prior: the agent you have not loaded is the one you will forget exists.

**Ambiguous terms** — `flywheel`, `round`, `round N`, `validation round`,
`verification round`, `validation_rounds.json`, generic `validate` / `validation`
without "consistency" or a specific module:
→ **ASK which agent before acting.** Cost of a wrong run is ~1 hour of compute and a
polluted validation_rounds.json.

**Quick recency check** (run before assuming):

```bash
python3 -c "import json,os
for label,path in [('magpie','magpie-agent/audit/validation_rounds.json'),('preproc','magpie-preproc-agent/feedback/validation_rounds.json')]:
  if os.path.exists(path):
    d=json.load(open(path)); r=d.get('rounds',[])
    print(f'{label}: {len(r)} rounds, latest R{r[-1].get(\"round\")} on {r[-1].get(\"date\")}' if r else f'{label}: 0 rounds')"
```

**Cues**:
- GAMS modules / `module_XX.md` / `vm_*` / `q*` / `equations.gms` → magpie-agent
- R packages / `calcOutput` / `readSource` / `pik-piam` / `.cs3` / `.mz` → preproc-agent
- Both or neither match → ASK explicitly, even in auto mode.

**Sentinels** — when confirming, use agent-prefixed labels: `magpie R3` / `preproc R3`,
never bare `R3`. Round numbers do **NOT** compare across agents.

**Discipline** — never edit the OTHER agent's files as collateral; never append to the
wrong validation_rounds.json.

(Origin: 2026-05-08 misroute incident — "round three" interpreted as magpie-agent re-test
when the user meant preproc-agent R3.)

## Lessons Learned

- 2026-07-31: hoisted here from AGENT.md. The hoist was gated for weeks on "trades
  always-loaded misroute-prevention for an on-demand trigger" — resolved by splitting the
  two: the trigger list stays always-loaded, the procedure moved here.
