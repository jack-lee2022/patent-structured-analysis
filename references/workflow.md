# Patent Structured Analysis Workflow (v3.0)

## Quick Start

### Claude Code (Recommended)

Simply provide a patent PDF path in natural language:

```
請分析這份專利：/path/to/US6702765.pdf
```

Claude Code auto-triggers the skill and produces `US6702765_analysis.md` + `US6702765_figures/`.

### CLI Usage (standalone Python)

```bash
# Analyze a patent from PDF — outputs JSON to stdout
python scripts/analyze_patent.py --pdf /path/to/patent.pdf

# Save JSON output to file
python scripts/analyze_patent.py --pdf /path/to/patent.pdf --output analysis.json

# Analyze from raw text
python scripts/analyze_patent.py --text "claims: ... description: ..."
```

### Python API

```python
from scripts.analyze_patent import StructuredPatentAnalyzerV2

analyzer = StructuredPatentAnalyzerV2()
result = analyzer.analyze(pdf_path="/path/to/patent.pdf")

print(result["claim_tree"])          # dict: claim_num → [dependent_on, ...]
print(result["claim_tree_mermaid"])  # Mermaid graph LR string
print(result["glossary"])            # dict: term → definition
```

---

## 5-Step Summary (v3.0)

| Step | Action | Tool / Method | Output |
|------|--------|---------------|--------|
| 1 | Extract full PDF text | PyMuPDF `fitz` | All pages text; detect scanned PDF |
| 2 | Detect & extract drawing sheets | Character-count scan + `get_pixmap(3x)` | `{PatentNo}_figures/FIG_sheet_N.png` |
| 3 | Parse patent structure | Text analysis | Bibliographic data, claims, components, references |
| 4 | Write structured `.md` report | 8-section Markdown template | `{PatentNo}_analysis.md` |
| 5 | Report to user | Summary output | File path + key findings (independent claims, core tech, status) |

> **Note on scanned PDFs**: If Step 1 returns empty text (all pages 0 chars), the skill falls back to saving pages as images and reading them visually. Pytesseract OCR is used as a secondary fallback if available.

---

## Report Sections

Every `{PatentNo}_analysis.md` contains these 8 sections:

| Section | Content |
|---------|---------|
| **基本資料** | 13-field bibliographic table including expiry status and PTA |
| **1. 專利摘要** | 2–4 paragraph abstract covering purpose, mechanism, modes, and applications |
| **2. 核心技術圖示** | 4–5 key figures selected for direct correspondence to independent claim elements |
| **3. 權利要求層次結構** | Mermaid `graph LR` claim dependency tree (all claims, Chinese labels) |
| **4. 關鍵術語定義** | Glossary table of 8+ key technical and legal terms with source references |
| **5. 技術組件清單** | All numbered components with 必要/選用 classification and technical description |
| **6. FTO / 迴避設計建議** | Infringement risk table + design-around table + expiry blockquote |
| **附錄：引用文獻** | Full list of cited US patents and academic literature |

---

## Key Figure Selection Logic (v3.0)

Section 2 limits figures to **4–5 key figures** selected by this priority:

1. System overview showing all/most independent claim elements
2. Exploded or cross-section view of the core mechanism
3. Comparison figure illustrating the key technical feature
4. Second-embodiment figure confirming claim breadth
5. (Optional) Dependent-claim figure if it represents the most complete functional combination

**Not selected**: dimension variants, alternative materials, or figures illustrating only a single dependent claim.

---

## Patent Expiry Calculation

| Filing Date | Applicable Law | Term |
|-------------|----------------|------|
| Before June 8, 1995 | Old law | 17 years from grant date |
| On/after June 8, 1995 | New law | 20 years from earliest filing date |
| Straddles both | Both apply | Take the **later** of the two dates |

Patent Term Adjustments (PTA) under 35 U.S.C. 154(b) are added to the term when present.  
Terminal Disclaimers tie the patent's term to an earlier family member — always verify the parent's expiry.

---

## Integration with patent-agent

This skill is designed to work with the patent-agent backend:

- `patents.db` table `patents` provides `claims`, `description`, `abstract`
- `patents.db` table `analyses` stores the structured analysis results

```sql
CREATE TABLE patents (
    id INTEGER PRIMARY KEY,
    patent_id TEXT UNIQUE,
    title TEXT,
    abstract TEXT,
    claims TEXT,
    description TEXT,
    publication_date TEXT,
    assignee TEXT
);

CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    patent_id TEXT,
    analysis_json TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patent_id) REFERENCES patents(patent_id)
);
```
