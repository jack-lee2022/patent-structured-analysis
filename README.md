# Patent Structured Analysis (v2.0)

A professional-grade skill for performing rigorous structured patent analysis. This tool transforms dense legal patent text into actionable technical data using a sophisticated 4-step workflow, now enhanced with Claim Tree visualization and Lexicographical analysis.

---

## What's New in v2.0

| Feature | Description |
| :--- | :--- |
| **Claim Tree Analysis** | Automatically parses and visualizes independent and dependent claim hierarchies using Mermaid diagrams. |
| **Auto-Glossary (Lexicographer)** | Scans the description for inventor-defined terms to ensure legal precision in technical interpretation. |
| **Dual-Pass Strategy** | Uses an "Anchor-Snippet" approach to handle extremely long patents without losing technical context. |
| **Mermaid Visualizations** | Generates both Component Architecture and Functional Logic diagrams. |

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

## Installation

### Hermes Agent

```bash
# Clone into your Hermes skills path
git clone git@github.com:jack-lee2022/patent-structured-analysis.git \
  ~/.hermes/skills/patent-structured-analysis
```

Hermes will auto-discover `SKILL.md` on startup and trigger the skill when you say:

- `分析專利`、`拆解專利`、`FTO分析`
- `獨立項分析`、`組件映射`、`附圖對應`
- `關鍵圖示`、`專利結構`、`專利拆解`

---

### Claude Code

Install the `.skill` package (zip-based skill bundle):

```bash
# Download the latest .skill release
curl -L -o patent-structured-analysis.skill \
  https://github.com/jack-lee2022/patent-structured-analysis/releases/latest/download/patent-structured-analysis.skill

# Install via Claude Code CLI
claude skills install patent-structured-analysis.skill
```

Or clone directly (Claude Code also supports folder-based skills):

```bash
claude skills add \
  --from git@github.com:jack-lee2022/patent-structured-analysis.git
```

---

### OpenClaw

OpenClaw uses the same folder-based skill structure as Hermes:

```bash
# Clone into OpenClaw's skills directory (default path)
git clone git@github.com:jack-lee2022/patent-structured-analysis.git \
  ~/.openclaw/skills/patent-structured-analysis

# Or via the OpenClaw CLI
openclaw skill install jack-lee2022/patent-structured-analysis
```

> OpenClaw skill auto-discovery is enabled by default. If disabled, add to your `openclaw.yaml`:
> ```yaml
> skills:
>   - path: ~/.openclaw/skills/patent-structured-analysis
>   ```

---

### Gemini (Google AI / Vertex AI)

Gemini does not use folder-based skills. Instead, load `SKILL.md` as a **system instruction** and expose the `analyze_patent` function via the **Function Calling** API.

#### Option A: System Instruction (Chat/Studio)

Copy the content of `SKILL.md` into the **System Instructions** field in Google AI Studio or Gemini API:

```python
from google import genai

client = genai.Client(api_key="YOUR_API_KEY")

# Load the skill as system instruction
with open("SKILL.md") as f:
    system_instruction = f.read()

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Analyze patent US11311692B2 for FTO",
    config=genai.types.GenerateContentConfig(
        system_instruction=system_instruction
    ),
)
```

#### Option B: Function Calling (API/Vertex AI)

Register the `analyze_patent` function so Gemini can call the script when needed:

```python
import subprocess
import json

analyze_patent_tool = {
    "name": "analyze_patent",
    "description": "Perform 4-step structured analysis on a patent (PDF, text, or DB ID)",
    "parameters": {
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "enum": ["patent_id", "pdf", "text"],
                "description": "Input type"
            },
            "value": {
                "type": "string",
                "description": "Patent ID, PDF path, or raw text"
            },
            "db_path": {
                "type": "string",
                "description": "SQLite DB path (required for patent_id source)"
            }
        },
        "required": ["source", "value"]
    }
}

def run_analysis(source, value, db_path=None):
    cmd = ["python3", "scripts/analyze_patent.py", f"--{source}", value]
    if db_path:
        cmd += ["--db", db_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

# Use with Gemini function calling
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Analyze patent US11311692B2",
    config=genai.types.GenerateContentConfig(
        tools=[analyze_patent_tool]
    ),
)
```

---

## Standalone Script Usage

The bundled Python script works without any AI agent:

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
