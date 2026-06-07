# Patent Structured Analysis Workflow

## Quick Start

### CLI Usage

```bash
# Analyze a patent from PDF
python scripts/analyze_patent.py --pdf /path/to/patent.pdf --output analysis.json

# Analyze from patent ID (requires patent-agent DB)
python scripts/analyze_patent.py --patent-id US6702765B2 --output analysis.json

# Analyze from raw text
python scripts/analyze_patent.py --text "claims: ... description: ..." --output analysis.json
```

### Python API

```python
from scripts.analyze_patent import StructuredPatentAnalyzer

analyzer = StructuredPatentAnalyzer()
result = analyzer.analyze_pdf("/path/to/patent.pdf")
print(result["step1_independent_claims_analysis"]["technical_problem"])
```

## 4-Step Summary

| Step | Input | Output | Purpose |
|------|-------|--------|---------|
| 1 | Independent claim(s) | Technical problem + solution + elements | Understand what the patent protects |
| 2 | Claim elements + description | Component list with optional/mandatory flags | Identify what you must avoid or can design around |
| 3 | Component list + patent figures | Figure-to-component mapping | Find the visual evidence for each component |
| 4 | All figures + Step 1 output | Hero figure + score + alternatives | Determine the single most representative illustration |

## Integration with patent-agent

This skill is designed to work with the patent-agent backend:

- `patents.db` table `patents` provides `claims`, `description`, `abstract`
- `patents.db` table `analyses` stores the structured analysis results
- The `collector.py` `_normalize_list_item()` method extracts raw patent data

## Database Schema (patent-agent)

```sql
CREATE TABLE patents (
    id INTEGER PRIMARY KEY,
    patent_id TEXT UNIQUE,
    title TEXT,
    abstract TEXT,
    claims TEXT,
    description TEXT,
    publication_date TEXT,
    assignee TEXT,
    -- ... other fields
);

CREATE TABLE analyses (
    id INTEGER PRIMARY KEY,
    patent_id TEXT,
    analysis_json TEXT,  -- stores the full 4-step JSON
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patent_id) REFERENCES patents(patent_id)
);
```
