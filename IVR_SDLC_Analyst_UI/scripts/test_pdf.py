import pdfplumber

with pdfplumber.open("CCR_HLD_PCI.pdf") as pdf:
    print(f"Total Pages Found in File: {len(pdf.pages)}")
    if len(pdf.pages) > 0:
        first_page = pdf.pages[0]
        print(f"Raw Text Length (No Crop): {len(first_page.extract_text() or '')}")
