import fitz  # This is PyMuPDF

doc = fitz.open("CCR_HLD_PCI.pdf")
print(f"Total Pages: {len(doc)}")

# Test extraction on the first page
first_page_text = doc[0].get_text()
print(f"Extracted Character Count: {len(first_page_text)}")

if len(first_page_text) > 0:
    print("\n--- First 200 Characters Sample ---")
    print(first_page_text[:200])
