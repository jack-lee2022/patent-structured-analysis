# Patent Structured Analysis (v3.0)

A professional-grade Claude Code skill for rigorous structured patent analysis. This tool transforms patent PDF documents into comprehensive structured Markdown reports, extracting original figures, building Claim Trees, and delivering FTO/design-around recommendations.

---

## What's New in v3.0

| Feature | Description |
| :--- | :--- |
| **PDF-Native Workflow** | Directly extracts full text and drawing sheets from patent PDFs using PyMuPDF — no copy-paste required. |
| **Original Figure Embedding** | Extracts all drawing sheet pages at 3× resolution and embeds them inline in the report. |
| **Complete Claim Tree** | Mermaid `graph LR` diagram covering all independent and dependent claims with Chinese labels. |
| **Structured .md Report** | Outputs a self-contained Markdown file with 10 defined sections, saved next to the source PDF. |
| **Patent Expiry Calculator** | Automatically computes expiry dates under both old law (17yr from grant) and new law (20yr from filing), taking the later date. |
| **FTO Tables** | Structured infringement risk tables and design-around strategy tables per independent claim. |

---

## When to Use

| Scenario | What This Skill Does |
|----------|---------------------|
| **Freedom-to-Operate (FTO)** | Identify mandatory claim elements you must avoid; receive design-around strategies |
| **Competitive Teardown** | Reverse-engineer a competitor's patent into structured technical components |
| **Claim Dissection** | Map all claims into a hierarchical Mermaid tree |
| **Patent Due Diligence** | Generate executive-ready reports for M&A, licensing, or investor review |
| **Expiry Verification** | Instantly confirm whether a patent is in-force or public domain |

---

## 5-Step Analysis Workflow

### Step 1 — Extract Full PDF Text
Uses PyMuPDF (`fitz`) to extract all pages, including cover (bibliographic data), specification (background, summary, detailed description), and all claims.

### Step 2 — Detect and Extract Drawing Sheets
Scans each page's character count to identify drawing sheets (typically < 200 chars). Extracts them as **3× resolution PNG** images into a `{PatentNo}_figures/` folder alongside the output report.

### Step 3 — Parse Patent Structure
Parses the full text to extract bibliographic data, abstract, figure descriptions, all component reference numbers, cited references, and every claim (identifying independent vs. dependent).

### Step 4 — Write Structured .md Report
Produces a complete Markdown file at `{PDF_directory}/{PatentNo}_analysis.md` using relative image paths — compatible with VS Code, Obsidian, Typora, and any Markdown viewer.

### Step 5 — Report to User
Confirms the saved file path and summarizes key findings (number of independent claims, core technology, patent status).

---

## Report Structure

Every report contains these 10 sections in order:

| Section | Content |
|---------|---------|
| **基本資料** | 13-field bibliographic table including expiry status |
| **1. 專利摘要** | 2–4 paragraph abstract covering purpose, mechanism, modes, and applications |
| **2. 核心技術圖示** | One subsection per drawing sheet with embedded PNG and technical caption |
| **3. 權利要求層次結構** | Mermaid `graph LR` claim dependency tree (all claims, Chinese labels) |
| **4. 關鍵術語定義** | Glossary table of 8–15 key technical and legal terms with source references |
| **5. 技術組件清單** | All numbered components with 必要/選用 classification and technical description |
| **6. FTO / 迴避設計建議** | Infringement risk table + design-around table + expiry blockquote |
| **附錄：引用文獻** | Full list of cited US patents and academic literature |

---

## Installation

### Claude Code (Recommended)

Copy the skill folder directly into your Claude Code skills directory:

```bash
git clone https://github.com/jack-lee2022/patent-structured-analysis.git \
  ~/.claude/skills/patent-structured-analysis
```

Claude Code will auto-discover `SKILL.md` and trigger the skill whenever you:
- Provide a patent PDF path and ask for analysis
- Say "分析這份專利", "analyze this patent", "patent FTO analysis"
- Ask for "claim dissection", "structured patent report", "freedom-to-operate"

No manual invocation required — the skill triggers automatically based on context.

### Hermes Agent

```bash
git clone https://github.com/jack-lee2022/patent-structured-analysis.git \
  ~/.hermes/skills/patent-structured-analysis
```

### OpenClaw

```bash
git clone https://github.com/jack-lee2022/patent-structured-analysis.git \
  ~/.openclaw/skills/patent-structured-analysis
```

---

## Usage Example

Simply provide a patent PDF path in natural language:

```
請分析這份專利：/path/to/US6702765.pdf
```

The skill will:
1. Extract all text and figures from the PDF
2. Save `US6702765_figures/FIG_sheet_1.png` … `FIG_sheet_N.png` (3× zoom)
3. Write `US6702765_analysis.md` with all sections and embedded figures
4. Confirm the output path

### Example Output Files

```
downloads/
├── US6702765.pdf                    ← input
├── US6702765_analysis.md            ← structured report
└── US6702765_figures/
    ├── FIG_sheet_1.png              ← Sheet 1 (3× resolution)
    ├── FIG_sheet_2.png              ← Sheet 2
    └── FIG_sheet_3.png              ← Sheet 3
```

### Convert Report to PDF

```bash
npx md-to-pdf US6702765_analysis.md
```

---

## Patent Expiry Calculation

The skill automatically computes expiry using the correct legal rule:

| Filing Date | Applicable Law | Term |
|-------------|----------------|------|
| Before June 8, 1995 | Old law | 17 years from grant date |
| On/after June 8, 1995 | New law | 20 years from earliest filing date |
| Straddles both | Both apply | Take the **later** of the two dates |

Patent Term Adjustments (PTA) under 35 U.S.C. 154(b) are also reflected when present on the cover page.

---

## Dependencies

| Package | Required | Purpose |
|---------|----------|---------|
| `python` ≥ 3.9 | **Yes** | Runtime |
| `PyMuPDF (fitz)` | **Yes** | PDF text extraction and figure rendering |

Install PyMuPDF:

```bash
pip install pymupdf
```

---

## License

MIT — part of the patent-agent project ecosystem.

---

## Related Projects

- [patent-agent](https://github.com/jack-lee2022/patent_agent) — Full patent collection, analysis, and reporting pipeline
- [patent-search-engine](https://github.com/jack-lee2022/patent-search-engine) — Multi-source patent search skill
