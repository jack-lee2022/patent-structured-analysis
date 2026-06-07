#!/usr/bin/env python3
"""
Patent Structured Analyzer — 4-step workflow
Same logic as patent-agent backend, packaged as a standalone script.
"""

import json
import re
import sqlite3
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path


try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class StructuredPatentAnalyzer:
    """
    4-step structured patent analyzer.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text from PDF and run 4-step analysis."""
        text = self._extract_pdf_text(pdf_path)
        if not text:
            return {"error": "Could not extract text from PDF", "patent_id": Path(pdf_path).stem}
        return self._analyze_text(text, patent_id=Path(pdf_path).stem)

    def analyze_patent_id(self, patent_id: str) -> Dict[str, Any]:
        """Fetch from patent-agent DB and analyze."""
        if not self.db_path:
            return {"error": "No DB path configured", "patent_id": patent_id}
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT patent_id, title, claims, description, abstract, assignee FROM patents WHERE patent_id=?",
            (patent_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return {"error": f"Patent {patent_id} not found in DB", "patent_id": patent_id}
        return self._analyze_from_db_row(row)

    def analyze_text(self, text: str, patent_id: str = "UNKNOWN") -> Dict[str, Any]:
        """Analyze raw patent text."""
        return self._analyze_text(text, patent_id=patent_id)

    # ------------------------------------------------------------------
    # PDF extraction
    # ------------------------------------------------------------------
    def _extract_pdf_text(self, pdf_path: str) -> str:
        if HAS_PDFPLUMBER:
            with pdfplumber.open(pdf_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        if HAS_PYMUPDF:
            doc = fitz.open(pdf_path)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        return ""

    # ------------------------------------------------------------------
    # 4-step analysis
    # ------------------------------------------------------------------
    def _analyze_text(self, text: str, patent_id: str) -> Dict[str, Any]:
        claims = self._extract_section(text, "claims", " Claims")
        description = self._extract_section(text, "description", " Description")
        abstract = self._extract_section(text, "abstract", " Abstract")

        if not claims:
            claims = abstract or text[:3000]

        step1 = self._step1_analyze_claims(claims)
        step2 = self._step2_map_components(claims, description)
        step3 = self._step3_diagram_correspondence(step2, description)
        step4 = self._step4_key_diagram(step3, step1)
        summary = self._overall_summary(step1, step2)

        return {
            "patent_id": patent_id,
            "title": self._extract_title(text),
            "step1_independent_claims_analysis": step1,
            "step2_necessary_components": step2,
            "step3_corresponding_diagrams": step3,
            "step4_key_diagrams": step4,
            "overall_summary": summary,
        }

    def _analyze_from_db_row(self, row) -> Dict[str, Any]:
        patent_id, title, claims, description, abstract, assignee = row
        text = f"Claims:\n{claims or ''}\n\nDescription:\n{description or ''}\n\nAbstract:\n{abstract or ''}"
        result = self._analyze_text(text, patent_id)
        result["title"] = title or result.get("title", "")
        result["assignee"] = assignee
        return result

    # ------------------------------------------------------------------
    # Step 1: Independent Claims Analysis
    # ------------------------------------------------------------------
    def _step1_analyze_claims(self, claims_text: str) -> Dict[str, Any]:
        """Extract problem, solution, elements from claims."""
        # Split into independent claims (lines starting with a number)
        claim_lines = re.split(r"\n\s*\d+\.", claims_text)
        if not claim_lines:
            claim_lines = [claims_text]

        # First element may be "What is claimed is:" preamble; skip it
        first_claim = ""
        for line in claim_lines:
            stripped = line.strip()
            if len(stripped) > 50 and not stripped.lower().startswith("what is claimed is"):
                first_claim = stripped[:1500]
                break
        if not first_claim:
            first_claim = claims_text.strip()[:1500]

        # Extract technical elements: look for "comprising" or "having" + list
        elements = []
        # Match everything after 'comprising:' and split by semicolons/newlines
        match = re.search(r"comprising\s*[:;]?(.*)", first_claim, re.IGNORECASE | re.DOTALL)
        if match:
            raw = match.group(1).strip()
            lines = raw.split("\n")
            for line in lines:
                line = line.strip().strip(";")
                # Stop at standalone 'wherein' clauses (not part of the list)
                if line.lower().startswith("wherein") and len(elements) > 0:
                    break
                if len(line) > 10 and len(line) < 300:
                    # Clean up the item: remove 'wherein' clause, relative clauses
                    clean = re.split(r"[,;]?\s*wherein", line, flags=re.IGNORECASE)[0].strip()
                    clean = re.split(r"[,;]?\s*configured to", clean, flags=re.IGNORECASE)[0].strip()
                    clean = re.split(r"[,;]?\s*for", clean, flags=re.IGNORECASE)[0].strip()
                    # Remove leading article
                    clean = re.sub(r"^(an?|the)\s+", "", clean, flags=re.IGNORECASE)
                    if clean and len(clean) > 5:
                        elements.append(clean)
        if not elements:
            # Fallback: extract noun phrases after articles
            elements = self._extract_noun_phrases(first_claim)[:6]
        if not elements:
            # Last resort: extract capitalized technical terms
            elements = self._extract_key_terms(first_claim)[:6]

        # Extract key terms
        key_terms = self._extract_key_terms(first_claim)

        return {
            "technical_problem": self._infer_problem(first_claim),
            "technical_solution": self._infer_solution(first_claim),
            "technical_elements": elements[:6],
            "key_terms": key_terms[:5],
            "function_and_purpose": self._infer_purpose(first_claim),
            "scope_and_limitations": self._infer_scope(first_claim),
        }

    # ------------------------------------------------------------------
    # Step 2: Necessary Components Mapping
    # ------------------------------------------------------------------
    def _step2_map_components(self, claims_text: str, description_text: str) -> List[Dict[str, Any]]:
        """Map each element to a component with optional flag and function."""
        step1 = self._step1_analyze_claims(claims_text)
        elements = step1["technical_elements"]
        components = []

        # For "comprising" claims, all listed elements are mandatory (cannot be omitted).
        # "is_optional" should be true only if the claim explicitly allows alternatives.
        is_optional = False
        if "consisting of" in claims_text.lower():
            is_optional = False
        elif "comprising" in claims_text.lower():
            is_optional = False  # Listed elements are required, list is just non-exhaustive
        elif "optionally" in claims_text.lower() or "may" in claims_text.lower():
            is_optional = True

        for elem in elements:
            function = self._find_component_function(elem, description_text)
            components.append({
                "component_name": elem,
                "is_optional": is_optional,
                "function": function,
            })
        return components

    # ------------------------------------------------------------------
    # Step 3: Diagram Correspondence
    # ------------------------------------------------------------------
    def _step3_diagram_correspondence(self, components: List[Dict], description_text: str) -> List[Dict]:
        """Find figure references for each component."""
        diagrams = []
        for comp in components:
            ref = self._find_figure_reference(comp["component_name"], description_text)
            diagrams.append({
                "component_name": comp["component_name"],
                "diagram_reference": ref["figure"],
                "diagram_description": ref["description"],
            })
        return diagrams

    # ------------------------------------------------------------------
    # Step 4: Key Diagram Identification
    # ------------------------------------------------------------------
    def _step4_key_diagram(self, diagrams: List[Dict], step1: Dict) -> Dict[str, Any]:
        """Select the hero figure."""
        if not diagrams:
            return {
                "primary_diagram": "None",
                "reasoning": "No figures available in source",
                "completeness_score": 0,
                "alternative_diagrams": [],
            }

        # Primary: figure referenced by most components
        figure_counts = {}
        for d in diagrams:
            fig = d["diagram_reference"]
            if fig and fig != "Not shown":
                figure_counts[fig] = figure_counts.get(fig, 0) + 1

        if not figure_counts:
            primary = diagrams[0]["diagram_reference"] if diagrams else "None"
        else:
            primary = max(figure_counts, key=figure_counts.get)

        # Score based on how many components it shows
        count = figure_counts.get(primary, 0)
        score = min(10, max(1, count * 2 + 2))

        # Alternatives: next most referenced
        sorted_figs = sorted(figure_counts, key=figure_counts.get, reverse=True)
        alternatives = [f for f in sorted_figs[1:3] if f != primary]

        return {
            "primary_diagram": primary,
            "reasoning": f"The primary diagram shows {count} key components, including the core innovation.",
            "completeness_score": score,
            "alternative_diagrams": alternatives,
        }

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def _overall_summary(self, step1: Dict, step2: List[Dict]) -> str:
        problem = step1["technical_problem"]
        solution = step1["technical_solution"]
        elements = ", ".join([c["component_name"] for c in step2[:3]])
        return f"本专利提出了{solution}，用于解决{problem}。核心组件包括{elements}。"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _extract_section(self, text: str, keyword: str, alt_keyword: str) -> str:
        """Extract a section from patent text."""
        # If text contains "What is claimed is:", treat claims as everything from that line
        # until the next major section header
        if keyword.lower() == "claims":
            m = re.search(r"(?i)(?:what is claimed is:|claims\s*[:\n]+)\s*(.*?)(?=\n\s*(?:description|abstract|summary|background|detailed description|fig|figure)\s*[:\n]|$)", text, re.DOTALL)
            if m:
                return m.group(1).strip()
        # Try common patterns for other sections
        patterns = [
            rf"(?i){keyword}\s*[:\n]+(.*?)(?=\n\s*(?:description|abstract|claims|summary|background|fig|figure)\s*[:\n]|$)",
            rf"(?i){alt_keyword}\s*[:\n]+(.*?)(?=\n\s*(?:description|abstract|claims|summary|background|fig|figure)\s*[:\n]|$)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.DOTALL)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_title(self, text: str) -> str:
        m = re.search(r"(?i)title[:\s\n]+(.+?)(?=\n|abstract|claims)", text)
        return m.group(1).strip() if m else ""

    def _extract_noun_phrases(self, text: str) -> List[str]:
        # Simple regex-based noun phrase extraction
        pattern = r"\b(?:a|an|the)\s+([a-zA-Z\s\-]+?)(?:\s+(?:for|with|having|comprising|wherein|and|or)\b|$|[,.])"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [m.strip() for m in matches if 3 < len(m.strip()) < 80]

    def _extract_key_terms(self, text: str) -> List[str]:
        # Extract technical terms (capitalized words, hyphenated words)
        # Exclude common stop words and legal/formal terms
        stop = {"What", "The", "A", "An", "This", "That", "These", "Those", "Claim", "Claims",
                "Wherein", "Comprising", "Consisting", "Having", "Being", "Said", "Each", "All",
                "One", "Two", "First", "Second", "Third", "Fourth", "Fifth", "At", "Least", "Most"}

        # Find multi-word technical terms: capitalized words, hyphenated words
        # Pattern: capitalized words with optional lowercase in between
        terms = re.findall(r"\b[A-Z][a-z]+(?:\s+[a-z]+)*\b", text)
        terms = [t for t in terms if t not in stop and len(t) > 3]

        # Also find hyphenated technical terms
        hyphens = re.findall(r"\b[a-z]+-[a-z]+(?:-[a-z]+)*\b", text, re.IGNORECASE)
        terms.extend([h for h in hyphens if len(h) > 5])

        return list(dict.fromkeys(terms))  # deduplicate while preserving order

    def _infer_problem(self, claim: str) -> str:
        # Look for "for [purpose]" or "to [solve]" patterns in the claim
        m = re.search(r"(?i)(?:for|to)\s+([a-z\s]+(?:treating|preventing|alleviating|managing|detecting|measuring|monitoring|controlling|improving|maintaining|reducing|eliminating|enhancing|diagnosing|therapy|treatment|detection|measurement|control|prevention|alleviation|management|maintenance|reduction|elimination|enhancement|diagnosis)\s+[a-z\s,]+)", claim)
        if m:
            return f"{m.group(1).strip()}"
        # Fallback: look for "problem" or "need"
        m = re.search(r"(?i)(?:problem|need|difficulty|challenge|issue)[\s:]*(.+?)(?:\.|\n)", claim)
        if m:
            return m.group(1).strip()
        return "尚未明确提出技術问题"

    def _infer_solution(self, claim: str) -> str:
        # Remove "What is claimed is:" prefix and claim preamble
        clean = re.sub(r"(?i)what is claimed is:\s*\d*\.\s*", "", claim).strip()
        # Look for apparatus/method/system/device
        m = re.search(r"(?i)(?:apparatus|method|system|device|composition|kit)\s+(?:for|of|to)\s+(.+?)(?:\.|\n)", clean)
        if m:
            return f"A {m.group(0).strip().lower()}"
        return clean[:200].strip()

    def _infer_purpose(self, claim: str) -> str:
        return self._infer_solution(claim)

    def _infer_scope(self, claim: str) -> str:
        if "comprising" in claim.lower():
            return "Open-ended: 'comprising' allows additional elements not listed"
        if "consisting of" in claim.lower():
            return "Closed-ended: 'consisting of' limits to exactly the listed elements"
        return "Scope depends on claim interpretation"

    def _find_component_function(self, component: str, description: str) -> str:
        # Extract the core noun phrase (remove trailing clauses)
        core = re.split(r'[,;]?\s*wherein', component, flags=re.IGNORECASE)[0].strip()
        core = re.split(r'[,;]?\s*configured to', core, flags=re.IGNORECASE)[0].strip()
        core = re.split(r'[,;]?\s*for', core, flags=re.IGNORECASE)[0].strip()
        core = re.sub(r'^(an?|the)\s+', '', core, flags=re.IGNORECASE)
        # Take first 3-4 words as search key
        search_key = ' '.join(core.split()[:4])
        sentences = re.split(r"(?<=[.!?])\s+", description)
        for sent in sentences:
            if search_key.lower() in sent.lower():
                # Try to extract verb phrase
                m = re.search(rf"(?i)(?:{re.escape(search_key)}|it|which)\s+(?:is|are|provides|configured|adapted|designed|used|serves|functions|operates|has)\s+(?:to|as|for)\s+(.+?)(?:\.|,|;)", sent)
                if m:
                    return f"to {m.group(1).strip()}"
                # Try simpler pattern: verb after component name
                m = re.search(rf"(?i){re.escape(search_key)}\s+\w+\s+(\w+\s+.+?)(?:\.|,|;)", sent)
                if m:
                    verb = m.group(1).strip()
                    return f"to {verb}"
        return f"to support the {core} function"

    def _find_figure_reference(self, component: str, description: str) -> Dict[str, str]:
        # Extract the core noun phrase for searching
        core = re.split(r'[,;]?\s*wherein', component, flags=re.IGNORECASE)[0].strip()
        core = re.split(r'[,;]?\s*configured to', core, flags=re.IGNORECASE)[0].strip()
        core = re.split(r'[,;]?\s*for', core, flags=re.IGNORECASE)[0].strip()
        core = re.sub(r'^(an?|the)\s+', '', core, flags=re.IGNORECASE)
        search_key = ' '.join(core.split()[:4])
        # Search for "FIG. X" or "Figure X" near the component mention
        sentences = re.split(r"(?<=[.!?])\s+", description)
        for sent in sentences:
            if search_key.lower() in sent.lower():
                fig_match = re.search(r"(?i)(?:fig\.?\s*\d+[a-z]?|figure\s*\d+[a-z]?)", sent)
                if fig_match:
                    fig = fig_match.group(0).strip()
                    return {"figure": fig, "description": f"illustration of {core}"}
        return {"figure": "Not shown", "description": f"no figure reference found for {core}"}


# ====================================================================
# CLI
# ====================================================================
def main():
    parser = argparse.ArgumentParser(description="Patent Structured Analyzer")
    parser.add_argument("--pdf", help="Path to patent PDF")
    parser.add_argument("--patent-id", help="Patent ID from patent-agent DB")
    parser.add_argument("--db", default="/home/rocky/patent-agent/data/patents.db", help="patent-agent DB path")
    parser.add_argument("--text", help="Raw patent text")
    parser.add_argument("--output", "-o", default="analysis.json", help="Output JSON path")
    args = parser.parse_args()

    analyzer = StructuredPatentAnalyzer(db_path=args.db)

    if args.pdf:
        result = analyzer.analyze_pdf(args.pdf)
    elif args.patent_id:
        result = analyzer.analyze_patent_id(args.patent_id)
    elif args.text:
        result = analyzer.analyze_text(args.text)
    else:
        parser.print_help()
        return

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Analysis saved to {args.output}")


if __name__ == "__main__":
    main()
