<!--
Doc-correction PR. The point of this template is that a reviewer can decide how much
scrutiny is owed BEFORE reading the argument. Fill in the tier honestly - overstating it
is the only way this template can fail. An agent-written description is persuasive by
construction; the evidence block, not the prose, is what a reviewer should act on.
-->

## Tier

Pick exactly one. This sets the review effort and nothing else in this PR overrides it.

- [ ] **A — mechanically verified.** A checker in `audit/tools/` flags the defect, and the fix
      follows from its output. No judgment involved. *Reviewer cost: ~1 minute, one command.*
- [ ] **B — code-verified.** Re-derived by reading the GAMS source this session; every claim
      carries a `file:line`. *Reviewer cost: ~5 minutes, one grep.*
- [ ] **C — judgment.** Wording, structure, emphasis, or a claim with no mechanical check.
      *Reviewer cost: full review. Say so plainly; do not dress a C up as a B.*

## The correction

| | |
|---|---|
| **Doc** | `<path>:<line>` |
| **Class** | `citation_off_by_small` / `citation_line_wrong` / `citation_identifier_absent` / `nondefault_realization_unflagged` / `other:` |

**Before** (verbatim from the doc):
```
```

**After** (verbatim):
```
```

## Why the current text is wrong

State the code truth with a `file:line` in the MAgPIE tree (`modules/`, `core/`, `config/`).
One defect, or one defect class, per PR — mixed PRs are slow to review and get stalled.

## Verification — commands the reviewer can re-run

```bash
# from the magpie-agent/ directory

# 1. the checker's own controls still pass (a checker with a dead check passes
#    its negatives vacuously — the positives are what prove it can still fire)
python3 audit/tools/<checker>.py --root .. --selftest

# 2. the defect, before and after
```

<details><summary>Expected output</summary>

```
```
</details>

## Provenance

- **Produced by:** `<model / agent>` on `<YYYY-MM-DD>`
- [ ] Every claim above was **re-derived against the GAMS source in this session**, not recalled
      and not inherited from another agent's report.

> **This is an LLM-generated proposal.** Unless Tier A is ticked, treat every claim in it as a
> hypothesis until you have run the commands above. A confident description is not evidence;
> several claims in this project's history were fluent, plausible, and wrong.

## Checks

- [ ] `bash scripts/validate_consistency.sh` → `errors=0`
      *(CI runs this on every PR with `VALIDATOR_STRICT=true`, so a red gate fails the build —
      you do not need to run it yourself, but the author should have.)*
- [ ] **No local absolute paths** in the diff, the commit messages, **or this description** — no
      macOS home directory, no cluster project tree, no Linux home tree. Use `<magpie-root>`, `~`,
      or a relative path. This repo is **public**, and the tracked-file scan reads neither commit
      messages nor PR bodies, so check both by hand.
      <!-- Deliberately described rather than spelled out: a literal example here would match the
           very scan it tells you to run, giving every future sweep a permanent false positive. -->
- [ ] **No colleague-identifying local detail.** An agent that runs `pwd` will happily paste your
      home directory into its own output — one grader did exactly that this session.
- [ ] No secrets, tokens, credentials, or pasted private data.
- [ ] Targets `mscrawford/magpie-agent`. **Not** pushed to `pik-piam/*` or `magpiemodel/*`.
- [ ] If `AGENT.md` was edited: deployed to both copies
      (`cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md`) — drift is a Check-10 failure.

## For the reviewer

Fast path by tier: **A** → run the command block, check it's green, merge.
**B** → run the block, then spot-check one cited `file:line` yourself.
**C** → read the argument; the evidence block will not settle it.

If a claim turns out to be wrong, say so on the PR — corrections get recorded in
`audit/global/agent_lessons.md` or the relevant `modules/module_XX_notes.md` so the next
session inherits the fix rather than repeating it.
