# Changelog

All notable releases of the **magpie-agent** (MAgPIE AI Documentation System) are
recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/).

This project versions *documentation maturity and agent machinery*, not a software
API. A release marks a release-granularity milestone in documentation accuracy
(tracked by the semantic-validation flywheel) and in the agent's tooling. For
continuous, commit-level state see `audit/validation_rounds.json`,
`audit/pipeline_audit_rounds.json`, `audit/BACKLOG.md`, and the git log.

## [1.1.0] - 2026-06-05

Headline: the documentation has been driven to a demonstrably-current,
accuracy-stabilized state, and the agent's reach now spans the full MAgPIE
pipeline (R preprocessing -> GAMS core -> R reporting).

### Validation
- Semantic-validation flywheel extended from **13 to 47 rounds**. Recent rounds
  R41-R47 scored **9.28-9.57** (R43 = 9.57, highest on record); the documentation
  periphery is stabilized; doc-quality is ~10; rounds now net few or zero doc bugs,
  all fixed in-round.
- Cumulative doc bugs across all rounds: **~892 found / ~653 fixed** (v1.0.0
  reported 291 / 256 at round 13).
- Syntactic validator hardened: **32 -> 43 checks, 0 errors**. Added a Check-10
  AGENT.md-vs-deployed-copy drift guard, equation-name drift pre-flag, comma-list
  multi-citation parsing, a body-citation false-positive guard, and advisory
  unit-claim and `.scale`-value checks; freshness re-anchored to canonical `develop`.
- Docs current with MAgPIE `develop` @ee98739fd (0 commits behind at release).

### Added
- **Twin-agent architecture.** A companion preprocessing agent (`PREPROC_AGENT.md`)
  now covers the R input-data pipeline (madrat, mrcommons, mrmagpie, mrland,
  mrwater, ...), with a twin-agent disambiguation protocol in `AGENT.md` to prevent
  misroutes between the two agents. (Absent at v1.0.0.)
- **magpie4 downstream reporting layer.** Version-pinned `report.mif` / IAMC-variable
  provenance via `agent/helpers/magpie4_reference.md` (`project/version_pins.json`,
  magpie4 2.70.0), guarded across rounds by regression questions G3/G4. (Absent at
  v1.0.0.)
- **Structural pipeline audits.** 8 rounds of multi-lens audits of the agent's own
  machinery, logged in `audit/pipeline_audit_rounds.json`. (New file since v1.0.0.)
- **20 anti-confabulation MANDATEs** in `agent/helpers/verifiers.md`, auto-loaded on
  GAMS-identifier / equation / realization / default triggers. (New helper since
  v1.0.0.)
- `/pipeline-audit` slash command.
- Auto-loading context helpers expanded from **12 to 17**.

### Changed
- **Open-work SSOT consolidated** into `audit/BACKLOG.md` (new since v1.0.0). The
  live `CURRENT_STATE.json` SSOT convention was retired (R6 audit, 2026-05-25) in
  favour of the `audit/` artifacts plus the git log; the v1.0 snapshot is kept as a
  frozen historical marker.
- `AGENT.md` trimmed under the auto-load size threshold, with binding rules hoisted
  into auto-loaded helpers (`verifiers.md`, etc.).

### Removed
- `/feedback` slash command (2026-05-24). The agent now records lessons directly into
  `modules/module_XX_notes.md`, helper `Lessons Learned` sections, and
  `audit/global/agent_lessons.md`; there is no external submission inbox.

(Slash-command count is unchanged at 10: `/pipeline-audit` added, `/feedback`
retired. Cross-module conservation docs unchanged at 6.)

## [1.0.0] - 2026-03-07

First release of the magpie-agent: a specialized AI assistant for the MAgPIE
land-use model.

### Added
- 46/46 module documentation files (230K+ words).
- 13-round semantic-validation flywheel (accuracy 6.7 -> 8.6 / 10).
- 291 doc bugs found, 256 fixed across validation rounds.
- 32-check syntactic validator (778 variables, 269 equations, 68 realizations,
  2231 citations).
- Three-layer maintenance protocol (syntactic + sync + semantic).
- 12 auto-loading context helpers.
- 10 slash commands: `/guide`, `/sync`, `/explain`, `/trace`, `/validate`,
  `/validate-module`, `/validate-semantic`, `/update`, `/feedback`, `/bootstrap`.
- 6 cross-module conservation / safety docs.
- Core architecture documentation suite.

[1.1.0]: https://github.com/mscrawford/magpie-agent/releases/tag/v1.1.0
[1.0.0]: https://github.com/mscrawford/magpie-agent/releases/tag/v1.0.0
