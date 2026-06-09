# Claude Code Installation

## Option 1: Manual clone (Recommended)

```bash
git clone https://github.com/jack-lee2022/patent-structured-analysis.git \
  ~/.claude/skills/patent-structured-analysis
```

Claude Code will auto-discover `SKILL.md` on next startup. To update the skill later:

```bash
git -C ~/.claude/skills/patent-structured-analysis pull
```

## Option 2: Install from `.skill` bundle

> **Note**: The `.skill` bundle is a ZIP snapshot. It may lag behind the latest `SKILL.md` in the repository. Prefer Option 1 for the most up-to-date version.

```bash
# Download the latest .skill release
curl -L -o patent-structured-analysis.skill \
  https://github.com/jack-lee2022/patent-structured-analysis/releases/latest/download/patent-structured-analysis.skill

# Extract to Claude Code's skills directory
unzip patent-structured-analysis.skill -d ~/.claude/skills/
```

## Usage

After installation, Claude Code will automatically trigger this skill when you say:

- `Analyze this patent for FTO`
- `Perform a structured teardown of patent US11311692B2`
- `請分析這份專利：/path/to/patent.pdf`
- `FTO analysis` / `claim dissection` / `structured patent report`

## How it works

Claude Code reads `SKILL.md` from the skills directory and executes the 5-step workflow using built-in tools (Bash, Read, Write). No additional configuration is needed — the skill is self-contained in `SKILL.md`.

## Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `PyMuPDF (fitz)` | PDF text extraction and figure rendering | `pip install pymupdf` |
| `pytesseract` *(optional)* | OCR fallback for scanned PDFs | `pip install pytesseract` + install Tesseract binary |
