# /propose-doc-fix — open a doc-correction PR against the central repo

**Purpose.** A colleague using the agent finds a doc claim that looks wrong. This command turns
that into a reviewable PR instead of a lost observation.

**The bar.** Everything you propose is an LLM claim until something mechanical or a re-derivation
against the GAMS source backs it. The PR template tiers on exactly that, and **the tier is the
only thing a reviewer needs to trust to budget their time.** Overstating it is the single way
this workflow fails.

---

## Step 0 — preconditions

- The doc lives in `magpie-agent/`. **Never** commit AI docs from the parent MAgPIE repo.
- Confirm the remote: `git remote -v`. PRs target **`mscrawford/magpie-agent`**.
  **Never** push to `pik-piam/*` or `magpiemodel/*` — those are read-only from here.
- If you are on `main`, branch first: `git switch -c docfix/<short-slug>`.

## Step 1 — establish the defect, and its tier, honestly

| tier | when | what you must produce |
|---|---|---|
| **A** | a checker in `audit/tools/` flags it and the fix follows from its output | the checker command + its before/after output |
| **B** | you re-derived it by reading the GAMS source this session | a `file:line` for every claim, and the grep that shows it |
| **C** | wording, structure, or a claim with no mechanical check | the argument, plainly labelled as judgment |

Checkers that produce tier-A findings today:

```bash
python3 audit/tools/check_citation_content.py    --root .. --docs '<glob>'   # cited file:line contains what it is cited for
python3 audit/tools/check_default_realization.py --root .. --docs '<glob>'   # non-default realization described without saying so
python3 audit/tools/check_answer_identifiers.py  --root .. --batch <file>    # names that do not exist
```

**Run each checker's `--selftest` first and paste the result.** A checker whose positive controls
do not fire is not evidence — a dead check passes its negative controls vacuously, which has
already happened once in this project.

## Step 2 — re-derive before you write anything

Read the GAMS source yourself. Do not rely on a module doc to prove another module doc wrong, and
do not inherit a claim from an earlier agent's report without re-deriving it. If the claim rests
on a realization, check `config/default.cfg` for the **default** — describing a non-default
realization as if it were active is the single most common defect class in this corpus.

If you cannot settle it from the code, that is a **tier C** at best, and often it should not be a
PR at all — record it in `modules/module_XX_notes.md` instead and say what is unresolved.

## Step 3 — make the smallest edit that fixes it

One defect, or one defect class, per PR. Mixed PRs stall in review.

## Step 4 — check before you push

```bash
bash scripts/validate_consistency.sh        # must end errors=0
```

Read the verdict as a **separate step before committing** — CI runs the same gate on the PR with
`VALIDATOR_STRICT=true`, so a red gate fails the build.

If you edited `AGENT.md`, it is a three-file operation:
`cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md` (drift is a Check-10 failure).

## Step 5 — scrub, then push

This repo is **public**, history included.

- No local absolute paths in the diff, the commit message, **or the PR body**. The tracked-file
  scan reads neither commit messages nor PR bodies — check both by hand.
- Watch your own tool output: an agent that runs `pwd` will paste a home directory into its
  report. That happened this session.
- No secrets, tokens, or pasted private data.

```bash
git push -u origin docfix/<short-slug>
gh pr create --fill --base main            # the repo template is applied automatically
```

## Step 6 — fill the template truthfully

`.github/pull_request_template.md` is applied for you. The parts people get wrong:

- **Tier** — pick the honest one.
- **Verification block** — commands a reviewer can paste, with the expected output. Not prose.
- **Provenance** — say which model produced it and tick the re-derivation box only if true.

## Step 7 — after review

If a reviewer shows the claim was wrong, record it so the next session inherits the correction:
`modules/module_XX_notes.md` for a module-specific fact, `audit/global/agent_lessons.md` if it is
system-wide. Then say so on the PR.

---

## Lessons Learned

- *2026-08-01* — Tiering by evidence class, rather than by how important the fix seems, is what
  makes these fast to review: the reviewer knows the scrutiny owed before reading the argument.
- *2026-08-01* — A doc that spells out a pattern a checker greps for will trip that checker.
  Describe the pattern instead of instantiating it; do not allowlist the doc.
