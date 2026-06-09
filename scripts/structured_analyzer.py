import sys
import re
import json
import fitz  # PyMuPDF

class StructuredAnalyzer:
    """
    Patent Structured Analyzer with Dual-Pass logic and Mermaid visualization.
    """
    
    def __init__(self):
        self.anchors = []

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF and preserve paragraph indicators if possible."""
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + "\n"
        return full_text

    def identify_anchors(self, claims_text, full_description):
        """
        Pass 1: Anchor Identification.
        Find component IDs (e.g., '102', '20') and paragraph tags (e.g., '[0045]').
        """
        # Find numeric IDs in claims (e.g., "housing (102)")
        ids = set(re.findall(r'\(?(\d{2,})\)?', claims_text))
        print(f"[PASS 1] Found component IDs: {ids}")
        
        anchors = []
        # Split description into paragraphs (rough approximation)
        paragraphs = re.split(r'\n\s*\n|\[\d{4}\]', full_description)
        
        for i, para in enumerate(paragraphs):
            for cid in ids:
                if cid in para:
                    anchors.append(i)
                    break
        
        self.anchors = sorted(list(set(anchors)))
        return self.anchors

    def get_dense_context(self, full_description, window=2):
        """
        Pass 2: Contextual Extraction.
        Extract snippets around anchors.
        """
        paragraphs = re.split(r'\n\s*\n|\[\d{4}\]', full_description)
        dense_paragraphs = []
        
        already_added = set()
        for anchor in self.anchors:
            start = max(0, anchor - window)
            end = min(len(paragraphs), anchor + window + 1)
            for j in range(start, end):
                if j not in already_added:
                    dense_paragraphs.append(paragraphs[j])
                    already_added.add(j)
        
        return "\n\n".join(dense_paragraphs)

    def generate_mermaid(self, structured_data, graph_type="component"):
        """
        Generate Mermaid syntax from structured JSON.
        graph_type: "component" | "claim_tree"
        """
        if graph_type == "claim_tree":
            mermaid = "graph LR\n"
            tree = structured_data.get("claim_tree", {})
            for claim, deps in tree.items():
                for dep in deps:
                    mermaid += f"    C{dep} --> C{claim}\n"
            return mermaid

        # Default component structure
        mermaid = "graph TD\n"
        components = structured_data.get("components", [])
        
        for comp in components:
            cid = comp.get("id", "Unknown")
            name = comp.get("name", "Unknown")
            mermaid += f"    C{cid}[{name} {cid}]\n"
            
            # Relationships
            for sub in comp.get("sub_components", []):
                sid = sub.get("id")
                sname = sub.get("name")
                mermaid += f"    C{cid} --> C{sid}[{sname} {sid}]\n"
        
        return mermaid

    def extract_claim_tree(self, claims_text):
        """
        Extract claim dependency tree.
        Example output: {"2": ["1"], "3": ["1"], "4": ["2", "3"]}
        """
        # Split by number markers (e.g., "1.", "Claim 1.")
        claim_blocks = re.split(r'(?:\n|\r\n|^)\s*(?:\d+\.|\(\d+\)|Claim\s+\d+\.?)', claims_text)
        
        tree = {}
        for i, block in enumerate(claim_blocks):
            if not block.strip() or i == 0: continue
            
            claim_num = str(i)
            # Find dependencies like "claim 1", "claims 1-3", "reivindicación 1"
            deps = re.findall(r'(?:claim|claims|reivindicaci\u00f3n|revendication)\s*(\d+)', block, re.IGNORECASE)
            if deps:
                tree[claim_num] = sorted(list(set(deps)), key=int)
                
        return tree

    def extract_definitions(self, description):
        """
        Scan for lexicographical definitions.
        Example: "The term 'X' means 'Y'."
        """
        glossary = {}
        # Patterns for definitions
        patterns = [
            r"term\s+['\"]([^'\"]+)['\"]\s+(?:means|is\s+defined\s+as|refers\s+to)\s+([^.]+)\.",
            r"['\"]([^'\"]+)['\"]\s+as\s+used\s+herein\s+(?:means|refers\s+to)\s+([^.]+)\.",
            r"definition\s+of\s+['\"]([^'\"]+)['\"]\s+is\s+([^.]+)\."
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for m in matches:
                term = m.group(1).strip()
                definition = m.group(2).strip()
                glossary[term] = definition
                
        return glossary

    def run_analysis_pipeline(self, pdf_path, claims_text):
        """Full pipeline execution."""
        print(f"[PIPELINE] Starting analysis for {pdf_path}")
        
        full_text = self.extract_text_from_pdf(pdf_path)
        
        # New Features
        claim_tree = self.extract_claim_tree(claims_text)
        glossary = self.extract_definitions(full_text)
        
        # Step 1: Identify Anchors
        anchors = self.identify_anchors(claims_text, full_text)
        print(f"[PIPELINE] Identified {len(anchors)} relevant paragraph anchors.")
        
        # Step 2: Dense Context
        dense_context = self.get_dense_context(full_text)
        
        return {
            "dense_context": dense_context,
            "anchor_count": len(anchors),
            "claim_tree": claim_tree,
            "claim_tree_mermaid": self.generate_mermaid({"claim_tree": claim_tree}, "claim_tree"),
            "glossary": glossary
        }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python structured_analyzer.py <pdf_path> <claims_text_file>")
        sys.exit(1)
        
    pdf = sys.argv[1]
    with open(sys.argv[2], "r", encoding="utf-8") as f:
        claims = f.read()
        
    analyzer = StructuredAnalyzer()
    result = analyzer.run_analysis_pipeline(pdf, claims)
    print(json.dumps(result, ensure_ascii=False, indent=2))
