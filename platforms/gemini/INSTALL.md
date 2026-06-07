# Gemini (Google AI / Vertex AI) Installation

Gemini does not support folder-based skills. Instead, use this skill in two ways:

## Option 1: System Instruction (Recommended for Studio/Chat)

Copy the content of `../../SKILL.md` into the **System Instructions** field in Google AI Studio or the Gemini API. Gemini will follow the 4-step workflow when asked to analyze patents.

### Google AI Studio
1. Open [Google AI Studio](https://aistudio.google.com/)
2. Create a new chat
3. Click **System Instructions**
4. Paste the full content of `SKILL.md`
5. Start chatting: `Analyze patent US11311692B2 for FTO`

### Gemini API (Python)

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
print(response.text)
```

---

## Option 2: Function Calling (Recommended for API/Vertex AI)

Register the `analyze_patent` function so Gemini can delegate the structured analysis to the Python script.

### 1. Define the tool

```python
import json
import subprocess
import google.genai as genai

analyze_patent_tool = {
    "name": "analyze_patent",
    "description": "Perform 4-step structured patent analysis on a patent document (PDF, text, or database ID). Returns a JSON object with independent claims analysis, component mapping, diagram correspondence, and key diagram identification.",
    "parameters": {
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "enum": ["patent_id", "pdf", "text"],
                "description": "Input type: patent_id from DB, local PDF file, or raw text"
            },
            "value": {
                "type": "string",
                "description": "The patent ID (e.g., US11311692B2), PDF file path, or raw patent text"
            },
            "db_path": {
                "type": "string",
                "description": "SQLite database path (required when source='patent_id')",
                "default": "/home/rocky/patent-agent/data/patents.db"
            }
        },
        "required": ["source", "value"]
    }
}
```

### 2. Implement the function

```python
def run_analysis(source: str, value: str, db_path: str = None):
    """Execute the patent analysis script."""
    cmd = ["python3", "scripts/analyze_patent.py", f"--{source}", value]
    if db_path:
        cmd += ["--db", db_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"error": result.stderr}
    return json.loads(result.stdout)

# Register with Gemini
client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Analyze patent US11311692B2",
    config=genai.types.GenerateContentConfig(
        system_instruction=open("SKILL.md").read(),
        tools=[analyze_patent_tool]
    ),
)

# If Gemini calls the function, handle it:
if response.function_calls:
    for fc in response.function_calls:
        if fc.name == "analyze_patent":
            result = run_analysis(
                fc.args["source"],
                fc.args["value"],
                fc.args.get("db_path")
            )
            # Send result back to Gemini
            follow_up = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Function result: {json.dumps(result)}",
            )
            print(follow_up.text)
```

---

## Option 3: Context Caching (Vertex AI / Long Context)

For Gemini 1.5 Pro (1M+ context), cache the entire `SKILL.md` + reference files as context:

```python
import google.genai as genai

client = genai.Client(vertexai=True, project="YOUR_PROJECT", location="us-central1")

# Upload SKILL.md as a context document
with open("SKILL.md", "rb") as f:
    doc = client.files.upload(file=f, display_name="patent-analysis-skill")

# Use the cached document in every request
response = client.models.generate_content(
    model="gemini-1.5-pro-002",
    contents=[doc, "Analyze patent US11311692B2"]
)
```

---

## Trigger Phrases

Gemini will respond with the 4-step analysis when you say:

- `Analyze patent [ID] for FTO`
- `Perform structured teardown of patent [ID]`
- `Map components of patent [ID]`
- `Identify key diagrams in patent [ID]`
- `分析專利 [ID]` / `拆解專利 [ID]` / `FTO分析`
- `獨立項分析` / `組件映射` / `附圖對應` / `關鍵圖示`

## Note

The Gemini `system_instruction` field has a length limit (typically ~32K tokens). The full `SKILL.md` is well within this limit. If you hit the limit, truncate the `references/example_analysis.json` section.
