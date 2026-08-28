import os
import re
import json
import pdfplumber

class LocalHLDTextExtractor:
    """Handles text extraction from local PDF files while maintaining structural layout."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target PDF file not found at: {file_path}")

    def extract_clean_text(self) -> str:
        """Extracts text page by page, filtering out headers and footers."""
        full_text_content = []
        
        print(f"[✔] Opening local HLD: {self.file_path}")
        with pdfplumber.open(self.file_path) as pdf:
            for idx, page in enumerate(pdf.pages):
                # Basic cropping bound to ignore extreme top/bottom header/footer noise
                page_height = page.height
                page_width = page.width
                
                # Bounding box: (x0, top, x1, bottom) - crops out top 5% and bottom 5%
                cropped_page = page.crop((0, page_height * 0.05, page_width, page_height * 0.95))
                text = cropped_page.extract_text(layout=False)
                
                if text:
                    full_text_content.append(text)
                    
        print(f"[✔] Successfully extracted text from {len(full_text_content)} pages.")
        return "\n\n".join(full_text_content)


class HLDAuditChunker:
    """Splits structural components into context-aware chunks for LLM security analysis."""
    def __init__(self, target_chunk_size=1200, overlap=200):
        self.chunk_size = target_chunk_size
        self.overlap = overlap
        
        # Regex to detect major architectural subsections (e.g., "1.2 Security", "### System Setup")
        self.header_pattern = re.compile(
            r'(?m)^(?:(?:[A-Z\d]+\.)+(?:\d+)?\s+[A-Z\s]{4,}|#{1,4}\s+.*|Section\s+[A-Z\d]+:?.*)$', 
            re.IGNORECASE
        )
        
        # Explicit priority flags for gap review
        self.audit_keywords = {
            "security": ["iam", "auth", "encryption", "tls", "rbac", "token", "secrets", "kms", "firewall", "vpc", "dmz"],
            "integration": ["api", "webhook", "grpc", "kafka", "mq", "payload", "schema", "rest", "endpoint", "middleware"]
        }

    def _extract_sections(self, text: str) -> list:
        matches = list(self.header_pattern.finditer(text))
        if not matches:
            return [("Global Overview / Context Missing", text)]
        
        sections = []
        if matches[0].start() > 0:
            sections.append(("Preamble / General Introduction", text[:matches[0].start()]))
            
        for i in range(len(matches)):
            start = matches[i].start()
            end = matches[i+1].start() if i + 1 < len(matches) else len(text)
            header_title = matches[i].group(0).strip()
            sections.append((header_title, text[start:end]))
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


# --- Orchestrated Local Runner Execution ---
if __name__ == "__main__":
    # 1. Define your path parameters
    # Place your target customer document file name below:
    INPUT_HLD_PATH = "CCR_HLD_PCI.pdf" 
    OUTPUT_JSON_CHUNKS = "prioritized_audit_chunks.json"

    # Quick runtime patch helper for demonstration testing
    if not os.path.exists(INPUT_HLD_PATH):
        print(f"[!] Warning: '{INPUT_HLD_PATH}' not spotted locally. Writing dummy layout for compilation check.")
        with open("sample_stub.txt", "w") as f:
            f.write("1.1 System Integration Overview\nThis lists the API endpoints and TLS policies.")
        # Simulating data directly for execution sanity block
        raw_hld_text = "1.1 System Integration Overview\nThis infrastructure utilizes clear IAM policies and rest endpoints."
    else:
        # 2. Extract Document Content
        extractor = LocalHLDTextExtractor(INPUT_HLD_PATH)
        raw_hld_text = extractor.extract_clean_text()

    # 3. Structural Chunking Execution
    # target_chunk_size is set around ~1000 to 1200 words for balanced performance
    chunker = HLDAuditChunker(target_chunk_size=1000, overlap=150)
    processed_chunks = chunker.create_audit_chunks(raw_hld_text)
    
    # 4. Save structured outputs for quick validation
    with open(OUTPUT_JSON_CHUNKS, "w", encoding="utf-8") as out_file:
        json.dump(processed_chunks, out_file, indent=2)
        
    print(f"\n[✔] Process Completed! Total optimized chunks ready for review: {len(processed_chunks)}")
    print(f"[✔] Compiled matrix saved locally at: {OUTPUT_JSON_CHUNKS}")
    
    # Print sample distribution metric
    security_focused_count = sum(1 for c in processed_chunks if "SECURITY" in c["metadata"]["audit_tags"])
    integration_focused_count = sum(1 for c in processed_chunks if "INTEGRATION" in c["metadata"]["audit_tags"])
    print(f"    ↳ Security Targets: {security_focused_count} chunks.")
    print(f"    ↳ Integration Targets: {integration_focused_count} chunks.")
