#!/usr/bin/env python3
"""
Patent Structured Analyzer v2.0
Enhanced with Claim Tree, Auto-Glossary, and Dual-Pass Strategy.
"""

import json
import re
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

class StructuredPatentAnalyzerV2:
    def __init__(self):
        self.anchors = []

    def _extract_pdf_text(self, pdf_path: str) -> str:
        if not HAS_PYMUPDF:
            return ""
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text

    def extract_claim_tree(self, claims_text: str) -> Dict[str, List[str]]:
        claim_blocks = re.split(r'(?:\n|\r\n|^)\s*(?:\d+\.|\(\d+\)|Claim\s+\d+\.?)', claims_text)
        tree = {}
        for i, block in enumerate(claim_blocks):
            if not block.strip() or i == 0: continue
            claim_num = str(i)
            deps = re.findall(r'(?:claim|claims|reivindicaci\u00f3n|revendication)\s*(\d+)', block, re.IGNORECASE)
            if deps:
                tree[claim_num] = sorted(list(set(deps)), key=int)
        return tree

    def extract_definitions(self, description: str) -> Dict[str, str]:
        glossary = {}
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

    def identify_anchors(self, claims_text: str, description: str) -> List[int]:
        ids = set(re.findall(r'\(?(\d{2,})\)?', claims_text))
        anchors = []
        paragraphs = re.split(r'\n\s*\n|\[\d{4}\]', description)
        for i, para in enumerate(paragraphs):
            for cid in ids:
                if cid in para:
                    anchors.append(i)
                    break
        self.anchors = sorted(list(set(anchors)))
        return self.anchors

    def get_dense_context(self, description: str, window=2) -> str:
        paragraphs = re.split(r'\n\s*\n|\[\d{4}\]', description)
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

    def generate_mermaid_claim_tree(self, tree: Dict[str, List[str]]) -> str:
        mermaid = "graph LR\n"
        for claim, deps in tree.items():
            for dep in deps:
                mermaid += f"    C{dep} --> C{claim}\n"
        return mermaid

    def analyze(self, pdf_path: Optional[str] = None, text: Optional[str] = None, claims: Optional[str] = None) -> Dict[str, Any]:
        if pdf_path:
            full_text = self._extract_pdf_text(pdf_path)
            patent_id = Path(pdf_path).stem
        else:
            full_text = text or ""
            patent_id = "UNKNOWN"

        # In a real scenario, we'd split full_text into claims and description
        # For simplicity, we assume 'claims' is provided or we extract it
        if not claims:
            # Simple heuristic: claims usually come after 'CLAIMS' or at the end
            claims_match = re.search(r'(?i)CLAIMS[:\s]+(.*)', full_text, re.DOTALL)
            claims_text = claims_match.group(1) if claims_match else full_text[:5000]
            description_text = full_text.replace(claims_text, "")
        else:
            claims_text = claims
            description_text = full_text

        claim_tree = self.extract_claim_tree(claims_text)
        glossary = self.extract_definitions(description_text)
        self.identify_anchors(claims_text, description_text)
        dense_context = self.get_dense_context(description_text)

        return {
            "patent_id": patent_id,
            "claim_tree": claim_tree,
            "claim_tree_mermaid": self.generate_mermaid_claim_tree(claim_tree),
            "glossary": glossary,
            "dense_context_preview": dense_context[:1000] + "...",
            "analysis_ready_context": claims_text + "\n\n" + dense_context
        }

def main():
    parser = argparse.ArgumentParser(description="Patent Structured Analyzer v2.0")
    parser.add_argument("--pdf", help="Path to patent PDF")
    parser.add_argument("--text", help="Raw patent text")
    parser.add_argument("--claims", help="Specific claims text")
    parser.add_argument("--output", help="Output JSON file")
    args = parser.parse_args()

    analyzer = StructuredPatentAnalyzerV2()
    result = analyzer.analyze(pdf_path=args.pdf, text=args.text, claims=args.claims)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
