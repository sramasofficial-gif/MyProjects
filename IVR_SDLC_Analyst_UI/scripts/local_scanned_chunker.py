import os
import re
import json
import pdfplumber
import easyocr
import numpy as np
from PIL import Image

class WindowsPDFOCRExtractor:
    """Extracts text from scanned/flattened print-to-file PDFs on Windows without Poppler."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        print("[⚡] Initializing Local OCR Processing Hub...")
        self.reader = easyocr.Reader(['en'], gpu=False)

    def extract_text(self) -> str:
        full_text_content = []
        print(f"[⚡] Scanning vector data frames from: {self.file_path}")
        
        with pdfplumber.open(self.file_path) as pdf:
            total_pages = len(pdf.pages)
            for idx, page in enumerate(pdf.pages):
                print(f"    ↳ OCR Scan: Rendering Page {idx + 1}/{total_pages}...")
                
                # Render page at 150 DPI for OCR balance
                page_image = page.to_image(resolution=150)
                pil_img = page_image.original
                img_np = np.array(pil_img)
                
                strings = self.reader.readtext(img_np, detail=0)
                if strings:
                    # Enforce a structural line break trailing every single page chunk
                    full_text_content.append("\n".join(strings) + "\n")
                    
        return "\n\n".join(full_text_content)


class HLDAuditChunker:
    """Splits structural components into context-aware chunks for LLM security analysis."""
    def __init__(self, target_chunk_size=1200, overlap=200):
        self.chunk_size = target_chunk_size
        self.overlap = overlap
        
        # Flexed header pattern for varying OCR layouts
        self.header_pattern = re.compile(
            r'(?m)^(?:\d+(?:\.\d+)*\s+[A-Z\s]{4,}|SECTION\s+[A-Z\d]+:?.*)$', 
            re.IGNORECASE
        )
        
        self.audit_keywords = {
            "security": ["iam", "auth", "encryption", "tls", "rbac", "token", "secrets", "kms", "firewall", "vpc", "dmz"],
            "integration": ["api", "webhook", "grpc", "kafka", "mq", "payload", "schema", "rest", "endpoint", "middleware"]
        }

    def _extract_sections(self, text: str) -> list:
        matches = list(self.header_pattern.finditer(text))
        
        # FIX 1: Safe exit loop if no structural header match targets exist
        if not matches:
            return [["Scanned Layout / Complete HLD Stream", text]]
        
        sections = []
        # FIX 2: Protected index check initialization
        if matches[0].start() > 0:
            sections.append(["Preamble / Introduction", text[:matches[0].start()]])
            
        for i in range(len(matches)):
            start = matches[i].start()
            end = matches[i+1].start() if i + 1 < len(matches) else len(text)
            header_title = matches[i].group(0).strip()
            sections.append([header_title, text[start:end]])
        return sections

    def _tag_chunk_focus(self, chunk_text: str) -> list:
        lower_text = chunk_text.lower()
        tags = []
        for domain, keywords in self.audit_keywords.items():
            if any(kw in lower_text for kw in keywords):
                tags.append(domain.upper())
        return tags

    def create_audit_chunks(self, raw_text: str) -> list:
        structured_sections = self._extract_sections(raw_text)
        final_chunks = []
        
        for header, section_content in structured_sections:
            words = section_content.split()
            
            if len(words) <= self.chunk_size:
                tags = self._tag_chunk_focus(section_content)
                final_chunks.append({
                    "metadata": {"parent_section": header, "audit_tags": tags},
                    "content": f"[Context: {header}] [Focus: {', '.join(tags)}]\n{section_content}"
                })
                continue
                
            start_idx = 0
            while start_idx < len(words):
                end_idx = start_idx + self.chunk_size
                chunk_words = words[start_idx:end_idx]
                chunk_text = " ".join(chunk_words)
                
                tags = self._tag_chunk_focus(chunk_text)
                final_chunks.append({
                    "metadata": {"parent_section": header, "audit_tags": tags, "split_block": True},
                    "content": f"[Context: {header} (Cont.)] [Focus: {', '.join(tags)}]\n{chunk_text}"
                })
                start_idx += (self.chunk_size - self.overlap)
                
        return final_chunks


if __name__ == "__main__":
    INPUT_HLD_PATH = "CCR_HLD_PCI.pdf" 
    OUTPUT_JSON_CHUNKS = "prioritized_audit_chunks.json"

    if not os.path.exists(INPUT_HLD_PATH):
        print(f"[!] Error: File '{INPUT_HLD_PATH}' not found in the current directory.")
    else:
        # 1. Run Local OCR Pipeline
        extractor = WindowsPDFOCRExtractor(INPUT_HLD_PATH)
        raw_hld_text = extractor.extract_text()

        # 2. Structural Component Chunking
        chunker = HLDAuditChunker(target_chunk_size=1000, overlap=150)
        processed_chunks = chunker.create_audit_chunks(raw_hld_text)
        
        # 3. Store Results
        with open(OUTPUT_JSON_CHUNKS, "w", encoding="utf-8") as out_file:
            json.dump(processed_chunks, out_file, indent=2)
            
        print(f"\n[✔] Completed! Total optimized chunks ready for review: {len(processed_chunks)}")
        print(f"[✔] Matrix data saved to local workspace: {OUTPUT_JSON_CHUNKS}")
        
        security_count = sum(1 for c in processed_chunks if "SECURITY" in c["metadata"]["audit_tags"])
        integration_count = sum(1 for c in processed_chunks if "INTEGRATION" in c["metadata"]["audit_tags"])
        print(f"    ↳ Security Targets Spotted: {security_count}")
        print(f"    ↳ Integration Targets Spotted: {integration_count}")
