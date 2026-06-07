# Patent Structured Analysis

A Hermes skill for performing rigorous 4-step structured patent analysis on any patent document (PDF, text, or database record). Extracted from the production `patent-agent` backend and packaged as a reusable, standalone skill.

---

## When to Use

| Scenario | What This Skill Does |
|----------|---------------------|
| **Freedom-to-Operate (FTO)** | Identify mandatory components you must avoid in your product |
| **Competitive Teardown** | Reverse-engineer a competitor's patent into concrete technical elements |
| **Design-Around / Invalidity** | Map which components are optional vs. mandatory, find gaps for circumvention |
| **Patent Landscape** | Batch-analyze a portfolio and extract structured data for due diligence |
| **Technical Due Diligence** | Generate executive summaries for M&A, licensing, or investor review |

---

## 4-Step Analysis Workflow

### Step 1 — Independent Claims Analysis
- **Input**: The independent claim(s)
- **Output**: Technical problem, solution, key elements, boundary terms, and scope limitations
- **Purpose**: Understand *what* the patent protects at its broadest level

### Step 2 — Necessary Components Mapping
- **Input**: Claim elements + patent description
- **Output**: Component list with `is_optional` flag and `function` description
- **Purpose**: Identify what you must avoid (mandatory) vs. what you can design around (optional)

### Step 3 — Diagram Correspondence
- **Input**: Components + patent figures
- **Output**: For each component, which figure illustrates it and what the figure shows
- **Purpose**: Find the visual evidence that supports each technical element

### Step 4 — Key Diagram Identification
- **Input**: All figures + Step 1 output
- **Output**: The single "hero figure" that best captures the invention, with a completeness score (1–10) and alternative candidates
- **Purpose**: Determine the one figure an engineer should look at first

---

## Installation (Hermes Agent)

This skill is automatically discovered if cloned into your Hermes skills directory:

```bash
# Clone into your Hermes skills path
git clone git@github.com:jack-lee2022/patent-structured-analysis.git \
  ~/.hermes/skills/patent-structured-analysis
```

Hermes will load `SKILL.md` on startup and trigger the skill whenever you use phrases like:

- `分析專利`、`拆解專利`、`FTO分析`
- `獨立項分析`、`組件映射`、`附圖對應`
- `關鍵圖示`、`專利結構`、`專利拆解`

---

## Standalone Script Usage

The bundled Python script works without Hermes:

```bash
# From patent-agent database
python scripts/analyze_patent.py \
  --patent-id US11311692B2 \
  --db /path/to/patents.db \
  --output analysis.json

# From PDF
python scripts/analyze_patent.py \
  --pdf /path/to/patent.pdf \
  --output analysis.json

# From raw text
python scripts/analyze_patent.py \
  --text "Claims: ... Description: ..." \
  --output analysis.json
```

### Python API

```python
from scripts.analyze_patent import StructuredPatentAnalyzer

analyzer = StructuredPatentAnalyzer(db_path="/path/to/patents.db")
result = analyzer.analyze_patent_id("US11311692B2")

print(result["step1_independent_claims_analysis"]["technical_problem"])
print(result["step4_key_diagrams"]["primary_diagram"])
```

---

## Output Format

The skill always produces a single JSON object with this exact structure:

```json
{
  "patent_id": "US11311692B2",
  "title": "Negative-pressure oral apparatus and method...",
  "step1_independent_claims_analysis": {
    "technical_problem": "...",
    "technical_solution": "...",
    "technical_elements": ["...", "..."],
    "key_terms": ["...", "..."],
    "function_and_purpose": "...",
    "scope_and_limitations": "..."
  },
  "step2_necessary_components": [
    {
      "component_name": "...",
      "is_optional": false,
      "function": "to ..."
    }
  ],
  "step3_corresponding_diagrams": [
    {
      "component_name": "...",
      "diagram_reference": "FIG. 1",
      "diagram_description": "..."
    }
  ],
  "step4_key_diagrams": {
    "primary_diagram": "FIG. 1",
    "reasoning": "...",
    "completeness_score": 8,
    "alternative_diagrams": ["FIG. 2", "FIG. 3"]
  },
  "overall_summary": "本专利提出了..."
}
```

---

## Integration with patent-agent

This skill is designed to work with the [patent-agent](https://github.com/jack-lee2022/patent_agent) backend:

| Source | How to Use |
|--------|-----------|
| `patents.db` | `patents` table provides `claims`, `description`, `abstract` |
| `patents.db` | `analyses` table stores the full 4-step JSON |
| `collector.py` | `_normalize_list_item()` extracts raw patent data for analysis |

Database schema (patent-agent):

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

---

## Dependencies

| Package | Required | Purpose |
|---------|----------|---------|
| `python` >= 3.9 | Yes | Runtime |
| `pdfplumber` | Optional | PDF text extraction (preferred) |
| `PyMuPDF (fitz)` | Optional | PDF text extraction (fallback) |

---

## License

MIT — extracted from the patent-agent project for standalone reuse.

---

## Related Projects

- [patent-agent](https://github.com/jack-lee2022/patent_agent) — Full patent collection, analysis, and reporting pipeline
- [patent-search-engine](https://github.com/jack-lee2022/patent-search-engine) — Multi-source patent search skill
