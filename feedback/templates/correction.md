---
type: correction
target: [e.g., module_70.md, AGENT.md, Core_Architecture.md]
severity: [high|medium|low]
date: YYYY-MM-DD
author: [optional - your name or username]
---

## What's Wrong

[Describe the error, outdated information, or inaccuracy you found]

## Correct Information

[What it should say instead. Be specific and cite sources if possible]

## How to Verify

[Commands to verify this correction, if applicable]

Examples:
```bash
# Count equations in module
grep "^[ ]*q70_" ../../modules/70_livestock/*/declarations.gms | wc -l

# Check specific line number
head -28 ../../modules/52_carbon/*/equations.gms | tail -6

# Search for parameter
grep -r "pm_carbon_density" ../../modules/52_carbon/
```

## References

[Source code files with line numbers, papers, or other documentation that support this correction]

Examples:
- modules/70_livestock/fbask_jan16/equations.gms:45-52
- Module_Dependencies.md Section 3.2
- Robinson et al. (2014) - Livestock methodology paper
