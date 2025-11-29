# Tool Usage Patterns for MAgPIE Agent

**Purpose**: Best practices for using AI assistant tools effectively and reliably when working with MAgPIE

**Last Updated**: 2025-11-29

---

## 🎯 FUNDAMENTAL PRINCIPLE: Path Explicitness

**ALWAYS use absolute paths or verify your location before using relative paths.**

**Why**: Working directories can shift during sessions, causing relative paths to break and leading to false conclusions about file existence.

---

## 🔧 Shell/Bash Tools: Command Execution

### Working Directory Awareness

**CRITICAL**: Shell tools typically maintain session state - working directory persists across calls.

#### The Problem

```bash
# Call 1: Change directory
cd ../modules

# Call 2: Later in session (working directory is STILL ../modules)
ls core_docs/  # ❌ FAILS - you're not where you think you are
```

**Result**: False conclusion "core_docs/ doesn't exist"

#### ✅ SOLUTION 1: Use Absolute Paths (RECOMMENDED)

```bash
# From <env> working directory: /Users/turnip/.../magpie-agent/

# ✅ ALWAYS WORKS:
ls /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/core_docs/

# ✅ BUILD FROM KNOWN BASE:
# If working directory is /magpie/magpie-agent/:
ls $(pwd)/core_docs/AI_Agent_Behavior_Guide.md

# ✅ For files in parent MAgPIE repo:
ls /Users/turnip/Documents/Work/Workspace/magpie/modules/50_nr_soil_budget/
```

#### ✅ SOLUTION 2: Verify Location First

```bash
# Check where you are
pwd
# Output: /Users/turnip/.../magpie/magpie-agent

# THEN use relative paths
ls core_docs/AI_Agent_Behavior_Guide.md  # ✅ Now safe
```

#### ✅ SOLUTION 3: Avoid cd Commands

```bash
# ❌ AVOID THIS PATTERN:
cd /foo/bar && ls files/

# ✅ PREFER THIS:
ls /foo/bar/files/

# ✅ OR THIS (if multiple commands needed):
(cd /foo/bar && ls files/ && cat data.txt)  # Subshell - doesn't affect session
```

### File Existence Verification

**DON'T conclude "file doesn't exist" from one failed command.**

#### ❌ WRONG: Single Failed Attempt

```bash
# Command fails
wc -l core_docs/AI_Agent_Behavior_Guide.md
# Error: No such file or directory

# ❌ WRONG CONCLUSION:
"The file doesn't exist"
```

#### ✅ CORRECT: Multi-Method Verification

```bash
# Method 1: Absolute path
ls /Users/turnip/.../magpie-agent/core_docs/AI_Agent_Behavior_Guide.md

# Method 2: Find from known root
find /Users/turnip/.../magpie-agent -name "AI_Agent_Behavior_Guide.md" -type f

# Method 3: Check git tracking
git ls-tree -r HEAD --name-only | grep "AI_Agent_Behavior_Guide"

# Method 4: Check both possible locations
ls core_docs/AI_Agent_Behavior_Guide.md 2>/dev/null || \
ls magpie-agent/core_docs/AI_Agent_Behavior_Guide.md 2>/dev/null || \
echo "Not found in expected locations - verifying with find..."

# Method 5: Ask user if uncertain
# "I'm having trouble locating file X. Can you confirm it exists and provide the path?"
```

### Path Quoting for Spaces

**ALWAYS quote paths with spaces**

```bash
# ❌ WRONG:
cd /Users/name/My Documents  # FAILS

# ✅ CORRECT:
cd "/Users/name/My Documents"

# ✅ CORRECT:
python "/path/with spaces/script.py"
```

### Command Chaining

**Use && for dependent operations, avoid ; unless failures are acceptable**

```bash
# ✅ DEPENDENT (stop if mkdir fails):
mkdir -p output && cp data.txt output/

# ✅ INDEPENDENT (both should run):
git fetch & git status  # Parallel

# ⚠️ USE CAREFULLY (; runs both even if first fails):
rm file.txt ; echo "File removed"  # Echo runs even if rm failed

# ❌ AVOID newlines (unless in quoted strings):
# command1
# command2
# These run sequentially but hard to reason about

# ✅ PREFER:
command1 && command2  # Sequential with error checking
```

### Detecting Directory Shifts

**Red flags that working directory changed:**

1. **Relative path suddenly fails**:
```bash
ls core_docs/  # Previously worked, now fails
→ Check with pwd
```

2. **Path prefix in find output**:
```bash
find . -name "foo.md"
→ ./magpie-agent/foo.md
# The "./magpie-agent/" means you're in parent directory
```

3. **Inconsistent file operations**:
```bash
ls modules/  # Works
ls core_docs/  # Fails
→ Directory structure doesn't match expectations
```

**Response**: Immediately run `pwd` to verify location

---

## 📖 Read Tool: Reading Files

### Always Use Absolute Paths

**The Read tool requires absolute paths in the file_path parameter.**

#### ✅ CORRECT Usage

```python
Read(
    file_path="/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_50.md"
)
```

#### ❌ WRONG Usage

```python
# ❌ Relative path:
Read(file_path="modules/module_50.md")

# ❌ Assuming working directory:
Read(file_path="./core_docs/file.md")
```

### Path Construction from <env>

**Use the working directory from <env> to build paths:**

```python
# <env> shows: Working directory: /Users/turnip/.../magpie-agent

# For AI docs (in current repo):
Read(file_path="/Users/turnip/.../magpie-agent/modules/module_50.md")

# For GAMS code (in parent repo):
Read(file_path="/Users/turnip/.../magpie/modules/50_nr_soil_budget/macceff_aug22/equations.gms")
```

### File vs. Directory Distinction

**Read tool can only read FILES, not directories**

```python
# ❌ WRONG: Trying to read directory
Read(file_path="/path/to/modules/")
# Error: Is a directory

# ✅ CORRECT: Read specific file
Read(file_path="/path/to/modules/module_50.md")

# ✅ For directory listing, use Bash:
Bash(command="ls -la /path/to/modules/")
```

### Large Files: Use offset and limit

```python
# For files > 2000 lines, read in chunks:

# Read first 1000 lines:
Read(file_path="/path/to/large.md", limit=1000)

# Read lines 1000-2000:
Read(file_path="/path/to/large.md", offset=1000, limit=1000)

# Or find specific section with grep first:
Bash(command='grep -n "Section Title" /path/to/large.md')
# Then read that section
```

---

## ✏️ Write/Edit Tools: Modifying Files

### Write Tool: Creating/Overwriting Files

**Write REQUIRES absolute paths**

#### ✅ CORRECT

```python
Write(
    file_path="/Users/turnip/.../magpie-agent/feedback/integrated/file.md",
    content="..."
)
```

#### ❌ WRONG

```python
# ❌ Relative path:
Write(file_path="feedback/integrated/file.md", content="...")
```

### Pre-Write Verification

**Before writing, verify the directory exists**

```bash
# Check parent directory exists
ls -d /path/to/parent/directory/

# If doesn't exist, create it
mkdir -p /path/to/parent/directory/

# Then write
Write(file_path="/path/to/parent/directory/newfile.md", content="...")
```

### Edit Tool: Must Read First

**CRITICAL**: Edit tool requires you to have read the file in the current session

```python
# ✅ CORRECT PATTERN:
# 1. Read file
Read(file_path="/path/to/file.md")

# 2. Then edit
Edit(
    file_path="/path/to/file.md",
    old_string="original text",
    new_string="modified text"
)

# ❌ WRONG (will fail):
Edit(file_path="/path/to/file.md", ...)  # Haven't read it this session!
```

### Edit Tool: Preserve Exact Formatting

**Match EXACTLY what appears in file, including indentation**

#### The Trap: Line Number Prefixes

When you read a file with Read tool, output shows:
```
   123→    some code here
```

Format: `spaces + line_number + tab + actual_content`

#### ✅ CORRECT: Match actual content AFTER the tab

```python
Edit(
    file_path="/path/to/file.gms",
    old_string="    some code here",  # Content AFTER line number prefix
    new_string="    modified code"
)
```

#### ❌ WRONG: Including line number prefix

```python
Edit(
    old_string="   123→    some code here",  # ❌ Line number isn't in file!
    new_string="   123→    modified code"
)
```

---

## 🔍 Grep Tool: Searching Code

### Path Parameter Usage

**Path parameter is optional and should be a directory or specific file**

#### ✅ CORRECT Usage

```python
# Default: Search in current working directory
Grep(pattern="vm_nr_eff")

# Search specific directory:
Grep(
    pattern="vm_nr_eff",
    path="/Users/turnip/.../magpie/modules/50_nr_soil_budget/"
)

# Search specific file:
Grep(
    pattern="vm_nr_eff",
    path="/Users/turnip/.../magpie-agent/modules/module_50.md"
)
```

#### ⚠️ Relative Paths (use carefully)

```python
# If you're CERTAIN of working directory:
Grep(pattern="vm_nr_eff", path="modules/")

# But safer to verify first:
Bash(command="pwd")  # Verify location
Grep(pattern="vm_nr_eff", path="modules/")
```

### Output Mode Selection

```python
# Just find files containing pattern:
Grep(pattern="vm_nr_eff", output_mode="files_with_matches")

# See actual matching lines:
Grep(pattern="vm_nr_eff", output_mode="content")

# Count matches per file:
Grep(pattern="vm_nr_eff", output_mode="count")
```

### Context Lines

```python
# Show 3 lines before and after matches:
Grep(pattern="equation", output_mode="content", C=3)

# Show 5 lines after:
Grep(pattern="TODO", output_mode="content", A=5)
```

---

## 🗂️ Glob Tool: Finding Files

### Pattern Syntax

**Use glob patterns, not regex**

```python
# ✅ CORRECT (glob patterns):
Glob(pattern="**/*.gms")           # All .gms files recursively
Glob(pattern="modules/module_*.md") # Module docs
Glob(pattern="**/equations.gms")   # All equations.gms files

# ❌ WRONG (regex - won't work):
Glob(pattern="module_[0-9]+\.md")  # This is regex, not glob!
```

### Path Parameter

```python
# Search from specific directory:
Glob(
    pattern="**/*.gms",
    path="/Users/turnip/.../magpie/modules/"
)

# Default: Search from current working directory
Glob(pattern="**/*.md")
```

### Common Patterns

```python
# All module documentation:
Glob(pattern="modules/module_*.md")

# All GAMS equation files:
Glob(pattern="../modules/**/equations.gms")

# Specific realization:
Glob(pattern="../modules/50_nr_soil_budget/macceff_aug22/*.gms")

# All files in directory (non-recursive):
Glob(pattern="core_docs/*.md")

# All files recursively:
Glob(pattern="**/*")
```

---

## 📂 Path Resolution: MAgPIE Directory Structure

### Understanding the Layout

```
/magpie/                          ← Parent: Main MAgPIE project
├── AGENT.md                      ← DEPLOYED copy (don't edit)
├── modules/                      ← GAMS modules (actual code)
│   ├── 50_nr_soil_budget/
│   └── ...
└── magpie-agent/                 ← Current working directory
    ├── AGENT.md                  ← SOURCE (edit this)
    ├── agent/
    │   └── commands/             ← Command definitions
    ├── modules/                  ← AI documentation (NOT GAMS!)
    │   ├── module_50.md
    │   └── ...
    └── core_docs/
        └── Tool_Usage_Patterns.md  ← You are here
```

### Path Resolution Rules

**From working directory** `/magpie/magpie-agent/`:

```bash
# AI docs (current repo):
./modules/module_50.md                          # ✅ Relative
/path/to/magpie-agent/modules/module_50.md      # ✅ Absolute (safer)

# GAMS code (parent repo):
../modules/50_nr_soil_budget/                   # ✅ Relative
/path/to/magpie/modules/50_nr_soil_budget/      # ✅ Absolute (safer)

# Deployed AGENT.md:
../AGENT.md                                     # ✅ Relative
/path/to/magpie/AGENT.md                        # ✅ Absolute (safer)
```

### Disambiguation: modules/ Ambiguity

**TWO different `modules/` directories!**

1. **AI documentation**: `./modules/` = `/magpie-agent/modules/` (markdown files)
2. **GAMS code**: `../modules/` = `/magpie/modules/` (GAMS code)

**Rule**: Always clarify which you mean!

```bash
# ✅ CLEAR: AI docs
ls ./modules/module_50.md

# ✅ CLEAR: GAMS code
ls ../modules/50_nr_soil_budget/macceff_aug22/equations.gms

# ❌ AMBIGUOUS (if directory changed):
ls modules/  # Which modules? AI or GAMS?
```

---

## 🧪 Testing Path Assumptions

### Before Relying on Relative Paths

Run this diagnostic:

```bash
# 1. Where am I?
pwd

# 2. What's here?
ls -la

# 3. Does expected path exist?
ls -d ./modules/ && echo "AI docs modules exists" || echo "Not found"
ls -d ../modules/ && echo "GAMS modules exists" || echo "Not found"

# 4. Verify specific file:
ls ./modules/module_50.md 2>/dev/null && echo "AI doc found" || echo "Not in expected location"
```

### After Directory Operations

If you've done `cd` or similar, verify location:

```bash
# What happened?
cd ../modules

# Where am I now?
pwd
# Expected: /Users/turnip/.../magpie/modules

# Verify I'm where I think I am:
ls 50_nr_soil_budget/  # GAMS module should exist here

# Return to base:
cd /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent
```

---

## 🎯 Quick Reference: Tool Path Requirements

| Tool | Path Type | Notes |
|------|-----------|-------|
| **Read** | Absolute required | file_path must be absolute |
| **Write** | Absolute required | file_path must be absolute |
| **Edit** | Absolute required | file_path must be absolute |
| **Bash** | Any (but use absolute) | Relative paths fragile due to working dir |
| **Grep** | Optional (directory or file) | Absolute safer; relative okay if verified |
| **Glob** | Optional (directory) | Absolute safer; relative okay if verified |

---

## 📋 Checklist: Before Any File Operation

- [ ] **Know your working directory**: Run `pwd` if uncertain
- [ ] **Use absolute paths** when possible (especially Read/Write/Edit)
- [ ] **Verify file existence** properly (don't conclude from single failure)
- [ ] **Disambiguate paths**: `./modules/` (AI) vs `../modules/` (GAMS)
- [ ] **Quote paths with spaces**: `"/path/with spaces/file.txt"`
- [ ] **Check parent directories exist** before writing
- [ ] **Read files before editing** (Edit tool requirement)

---

## 🐛 Common Mistakes and Fixes

### Mistake 1: "File doesn't exist" conclusion

```bash
# ❌ ONE failed attempt:
ls core_docs/AI_Agent_Behavior_Guide.md
# Error → "File doesn't exist"

# ✅ VERIFY with multiple methods:
pwd  # Where am I?
find . -name "AI_Agent_Behavior_Guide.md"
git ls-tree -r HEAD --name-only | grep "AI_Agent_Behavior"
```

### Mistake 2: Relative paths after cd

```bash
# ❌ FRAGILE:
cd ../modules
ls 50_nr_soil_budget/  # Works now, but working dir changed for ALL future commands

# Later:
ls core_docs/  # ❌ FAILS - you're still in ../modules!

# ✅ SAFER:
ls ../modules/50_nr_soil_budget/  # No cd, working dir unchanged
```

### Mistake 3: Wrong modules/ directory

```bash
# ❌ AMBIGUOUS (which modules?):
ls modules/module_50.md

# ✅ EXPLICIT:
ls ./modules/module_50.md           # AI docs
ls ../modules/50_nr_soil_budget/    # GAMS code
```

### Mistake 4: Forgetting to read before edit

```python
# ❌ FAILS:
Edit(file_path="/path/to/file.md", old_string="...", new_string="...")
# Error: Must read file first

# ✅ CORRECT:
Read(file_path="/path/to/file.md")
Edit(file_path="/path/to/file.md", old_string="...", new_string="...")
```

### Mistake 5: Including line number prefix in edit

```python
# Read tool shows:
#    123→    some code here

# ❌ WRONG:
Edit(old_string="   123→    some code here", ...)

# ✅ CORRECT (match content AFTER tab):
Edit(old_string="    some code here", ...)
```

---

## 🎓 Learning From Real Examples

### Example 1: The Directory Navigation Error (2024-10-24)

**What happened**: Failed to find `core_docs/AI_Agent_Behavior_Guide.md`

**Mistake**:
```bash
wc -l core_docs/AI_Agent_Behavior_Guide.md
# Error: No such file or directory
# Concluded: "File doesn't exist"
```

**What went wrong**:
- Working directory had shifted from `/magpie-agent/` to `/magpie/`
- Relative path broke
- Didn't verify with absolute path or `pwd`

**Correct approach**:
```bash
# Method 1: Absolute path
wc -l /Users/turnip/.../magpie-agent/core_docs/AI_Agent_Behavior_Guide.md

# Method 2: Verify location first
pwd  # Shows: /magpie (not expected /magpie-agent)
# Now understand why relative path failed

# Method 3: Find it
find . -name "AI_Agent_Behavior_Guide.md"
# Shows: ./magpie-agent/core_docs/AI_Agent_Behavior_Guide.md
# (The ./magpie-agent/ prefix reveals you're in parent dir)
```

**Lesson**: Always use absolute paths or verify `pwd` first. Don't conclude "doesn't exist" from one relative path failure.

**See**: `feedback/integrated/20251024_220843_global_bash_directory_navigation.md`

---

## ✨ Best Practices Summary

### DO:
- ✅ Use absolute paths whenever possible
- ✅ Run `pwd` before using relative paths
- ✅ Verify file existence with multiple methods
- ✅ Quote paths with spaces
- ✅ Read files before editing
- ✅ Be explicit about `./modules/` vs `../modules/`
- ✅ Test path assumptions when uncertain

### DON'T:
- ❌ Assume working directory stayed constant
- ❌ Conclude "doesn't exist" from one failure
- ❌ Use `cd` unless necessary (prefer absolute paths)
- ❌ Mix up AI docs (`./modules/`) and GAMS code (`../modules/`)
- ❌ Forget to verify parent directories exist before writing
- ❌ Edit files without reading them first

---

## 📚 Related Documentation

- **AGENT.md**: General agent instructions and workflows
- **Response_Guidelines.md**: Response patterns and query routing
- **feedback/integrated/20251024_220843_global_bash_directory_navigation.md**: Detailed analysis of directory navigation errors

---

**Document Status**: ✅ Complete
**Created**: 2024-10-24
**Updated**: 2025-11-29 (model-agnostic refactor)
**Purpose**: Prevent tool usage errors and improve reliability
