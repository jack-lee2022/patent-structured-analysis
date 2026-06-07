# Claude Code Installation

## Option 1: Install from `.skill` bundle (recommended)

```bash
# Download the latest .skill release
curl -L -o patent-structured-analysis.skill \
  https://github.com/jack-lee2022/patent-structured-analysis/releases/latest/download/patent-structured-analysis.skill

# Install via Claude Code CLI
claude skills install patent-structured-analysis.skill
```

## Option 2: Install from Git repository

```bash
claude skills add \
  --from git@github.com:jack-lee2022/patent-structured-analysis.git
```

## Option 3: Manual clone

```bash
# Clone to Claude Code's skills directory
# (default: ~/.claude/skills/ or project-specific .claude/skills/)
git clone git@github.com:jack-lee2022/patent-structured-analysis.git \
  ~/.claude/skills/patent-structured-analysis
```

## Usage

After installation, Claude Code will automatically trigger this skill when you say:

- `Analyze this patent for FTO`
- `Perform a structured teardown of patent US11311692B2`
- `Map the components of this patent`
- `What are the key diagrams in this patent?`

## About `.skill` files

`.skill` is a zip-based bundle format used by Claude Code for distributing skills. It contains:
- `SKILL.md` — The skill definition with YAML frontmatter and instructions
- `scripts/` — Executable scripts for deterministic tasks
- `references/` — Reference documents loaded on demand

The skill is loaded into context when Claude Code detects a matching task.
