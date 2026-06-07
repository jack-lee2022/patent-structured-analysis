# OpenClaw Installation

## Option 1: Auto-discovery (recommended)

```bash
# Clone into OpenClaw's default skills directory
git clone git@github.com:jack-lee2022/patent-structured-analysis.git \
  ~/.openclaw/skills/patent-structured-analysis

# OpenClaw will auto-discover on next startup
```

## Option 2: Via CLI

```bash
openclaw skill install jack-lee2022/patent-structured-analysis
```

## Option 3: Manual configuration

Add to your `openclaw.yaml`:

```yaml
skills:
  - name: patent-structured-analysis
    path: ~/.openclaw/skills/patent-structured-analysis
    auto_trigger: true
```

## Usage

After installation, OpenClaw will trigger this skill when you use phrases like:

- `分析專利` / `Analyze patent` / `FTO analysis`
- `拆解專利` / `Teardown patent` / `Patent structure`
- `獨立項分析` / `Independent claim analysis`
- `組件映射` / `Component mapping`
- `附圖對應` / `Diagram correspondence`
- `關鍵圖示` / `Key diagrams`

## About OpenClaw Skills

OpenClaw supports the same folder-based skill structure as Hermes:
- `SKILL.md` — Skill definition with YAML frontmatter and markdown instructions
- `scripts/` — Executable scripts for deterministic tasks
- `references/` — Reference documents loaded on demand

The skill is triggered by description matching in the YAML frontmatter.
