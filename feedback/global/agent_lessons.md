# AI Agent Lessons - System-Wide Learnings

**Last Updated**: 2025-11-27
**Purpose**: Accumulated lessons about agent behavior, patterns, and improvements

---

## 🎯 How This File Is Used

This file contains **system-wide lessons** that apply across all modules and interactions.
It is updated automatically when the agent discovers system-wide insights, or manually during feedback integration.

The agent should consult this file for:
- Cross-cutting behavioral patterns
- Common mistakes to avoid
- Workflow improvements
- Response quality guidelines

---

## 📚 Integrated Lessons

### 1. Carbon Sequestration Depends on Age Class Maturation
New forests start at age class 1 with low carbon density. Carbon accumulation follows Chapman-Richards growth curves via `pm_carbon_density_ac(t,j,ac,"vegc")` (Module 52 × Module 28 interaction). Don't expect immediate carbon gains from afforestation — it takes 20-50 years for meaningful sequestration. Always check `vm_land_ac` age class distribution, not just total forest area.
*Source: 20251022 lesson_learned_module_52*

### 2. NEVER Commit AI Docs to Main MAgPIE Repo
The `.claude/commands/` files and `AGENT.md` live in the **magpie-agent** repo only. Committing them to the main MAgPIE repo violates the workflow. Always verify which git repo you're in before committing. The `/update` command handles deployment — trust the process.
*Source: 20251023 global_git_workflow*

### 3. "Calculated" ≠ "Mechanistic"
CRITICAL ERROR PATTERN: Do not conflate "uses equations with fixed parameters" with "mechanistic process-based modeling." MAgPIE uses many parameterized relationships (fixed coefficients from external data) that are NOT mechanistic simulations. Apply the three-check test: (1) equation structure, (2) parameter source, (3) dynamic feedback. See `Query_Patterns_Reference.md` Pattern 4.
*Source: 20251024 global_calculated_vs_mechanistic*

### 4. Always Use Absolute Paths in Bash
When using bash commands, always `cd` to the correct directory explicitly. Don't rely on assumed working directory state. The magpie-agent directory is `magpie-agent/` inside the main MAgPIE repo. GAMS code is at `../modules/XX_name/`. See `Tool_Usage_Patterns.md` for complete guidelines.
*Source: 20251024 global_bash_directory_navigation*

### 5. Don't Make Unverified Performance Claims About GAMS
The claim "multi-index sum is faster than nested sum" had NO official GAMS documentation support. Never assert performance differences without citing official sources. Both `sum((i,j), expr)` and `sum(i, sum(j, expr))` are mathematically equivalent; GAMS documentation makes no speed comparison. When uncertain, state "both are valid" without performance ranking.
*Source: 20251104 correction_gams_sum_performance*

### 6. AGENT.md Organization Matters
The AGENT.md file (formerly CLAUDE.md) serves as the agent's primary instruction set. Keep it organized with clear section headers, prioritize the most important rules at the top (MOST IMPORTANT RULE section), and always link to detailed docs rather than duplicating content. The document hierarchy (AGENT.md → module docs → core docs → GAMS code) must be respected.
*Source: 20251023 global_CLAUDE.md (file renamed to AGENT.md)*

---

## 🔄 Integration History

| Date | Feedback ID | Summary |
|------|-------------|---------|
| 2026-03-06 | 20251022_132243_lesson_learned_module_52 | Carbon + age class maturation |
| 2026-03-06 | 20251023_140229_global_CLAUDE.md | CLAUDE.md organization |
| 2026-03-06 | 20251023_180416_global_git_workflow | Don't commit to wrong repo |
| 2026-03-06 | 20251024_215608_global_calculated_vs_mechanistic | Calculated ≠ mechanistic |
| 2026-03-06 | 20251024_220843_global_bash_directory_navigation | Absolute paths in bash |
| 2026-03-06 | 20251104_205109_correction_gams_sum_performance | Unverified GAMS performance claim |
