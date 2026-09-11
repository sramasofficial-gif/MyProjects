"""
Confluence Wiki Reader - Enterprise Section Extractor & Structural Analyzer
===========================================================================
"""

import sys
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup

CONFLUENCE_BASE_URL = "https://reqcentral.com"   # no trailing slash
AUTH_STATE_FILE = "entra_auth_state.json"         #

# ===========================================================================
# STEP 1: Interactive Login (Unchanged)
# ===========================================================================
def do_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(CONFLUENCE_BASE_URL)

        print("\n--- ACTION REQUIRED ---")
        print("A browser window has opened.")
        print("1. Log in with your customer credentials.")
        print("2. Approve the passkey/MFA prompt on your phone.")
        print("3. Wait until the wiki page fully loads.")
        input("Once logged in successfully, press Enter here to continue...")

        context.storage_state(path=AUTH_STATE_FILE)
        print(f"\nSession saved to {AUTH_STATE_FILE}.")
        browser.close()

# ===========================================================================
# 🟢 STEP 2: ADVANCED HTML PARSING, CLASSIFICATION, AND MATRIX RENDERING
# ==============================================================================
def read_page(url):
    # Enforce safe console output streams to handle special characters on Windows
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')

    if not Path(AUTH_STATE_FILE).exists():
        print(f"No saved session found ({AUTH_STATE_FILE}). Run 'login' first.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_STATE_FILE)
        page = context.new_page()

        print("[🔍] Loading remote target Confluence wiki canvas link...")
        page.goto(url)
        page.wait_for_load_state("domcontentloaded")

        selectors_to_try = [
            "[data-testid='content-body']", 
            "#main-content",                  
            ".ak-renderer-document",          
        ]

        html_content = None
        for selector in selectors_to_try:
            if page.locator(selector).count() > 0:
                html_content = page.locator(selector).first.inner_html()
                break

        if html_content is None:
            print("[⚠️] Known content main selector absent. Snapping full body DOM tree layout instead.")
            html_content = page.locator("body").inner_html()

        browser.close()

    # -----------------------------------------------------------------------
    # BEAUTIFUL SOUP GRANULAR SECTION PARSER & CONTENT MATRIX CLASS ENGINES
    # -----------------------------------------------------------------------
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Clean up standard Confluence macro metadata elements to prevent duplicate indexing
    for ignore_tag in soup.select(".toc-macro, .confluence-toc, script, style"):
        ignore_tag.extract()

    # Locate structural heading tags across standard operational layouts
    heading_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    # Compile text contents sequentially by evaluating inter-heading node lists
    sections_matrix = []
    
    # Standard RegEx pattern checking for main and sub-section decimal numbering configurations
    numbered_heading_regex = re.compile(r'^\s*📊?\s*\d+(\.\d+)*')

    for i, heading in enumerate(heading_tags):
        heading_text = heading.get_text().strip()
        
        # Rule 3 Check: Filter headings to match numbered layouts if available
        # If the file contains un-numbered blocks, this safely preserves baseline layout markers
        is_numbered = bool(numbered_heading_regex.match(heading_text))
        
        # Deduce content nodes residing between current heading block and upcoming sibling heading
        content_fragments = []
        current_node = heading.next_sibling
        
        while current_node and current_node not in heading_tags:
            content_fragments.append(current_node)
            current_node = current_node.next_sibling

        # Initialize sub-tree parsers over matching section ranges
        section_soup = BeautifulSoup("".join([str(n) for n in content_fragments]), "html.parser")
        
        # --- DETECT CONTENT INVENTORY TYPES MANIFEST ---
        detected_types = []
        
        # 📊 1. Table Detection Checking
        if section_soup.find('table'):
            table_count = len(section_soup.find_all('table'))
            detected_types.append(f"📋 Table ({table_count}x)")
            
        # 🖼 2. Diagram / Imagery Schema Detection
        # Tracks common structural image nodes and Confluence diagram rendering attachments
        if section_soup.find(['img', 'svg']) or section_soup.select(".confluence-embedded-image, [data-macro-name='gliffy'], [data-macro-name='drawio']"):
            img_count = len(section_soup.find_all('img')) or 1
            detected_types.append(f"🖼 Diagram/Image ({img_count}x)")
            
        # 💻 3. Source Code Code-Block Ingestion Tracking
        if section_soup.find('pre') or section_soup.select(".code, .syntaxhighlighter"):
            detected_types.append("💻 Code Block")
            
        # 📝 4. Baseline Text/Paragraph Character Block Check
        text_payload = section_soup.get_text().strip()
        if len(text_payload) > 10:
            detected_types.append("📝 Text Content")

        # Fallback to empty if heading block acts solely as an indexing placeholder line
        if not detected_types:
            detected_types.append("📂 Empty Placeholder")

        sections_matrix.append({
            "index": i + 1,
            "heading": heading_text,
            "level": heading.name.upper(),
            "content_types": ", ".join(detected_types),
            "is_numbered": is_numbered
        })

    # -----------------------------------------------------------------------
    # ENTERPRISE CLASS TABLE VIEW GENERATOR MOCK DESK RENDERER
    # -----------------------------------------------------------------------
    print("\n" + "="*95)
    print("🎙️  ENTERPRISE SDLC BLUEPRINT ANALYST MATRIX - SPECIFICATION REVIEW SHEET")
    print("="*95)
    print(f"Target URL: {url}")
    print(f"Total Structural Sections Parsed: {len(sections_matrix)}")
    print("-"*95 + "\n")

    # Draw pure markdown checklist table layout structure grid headers
    print(f"| {'Sel'} | {'ID'}  | {'Lvl'} | {'Section Heading Title Descriptor'} ".ljust(55) + f"| {'Detected Content Types Inventory'} ")
    print(f"|-------|------|-------|-----------------------------------------------------|----------------------------------")

    for sec in sections_matrix:
        # Construct standard enterprise checkpoint mock selector flags
        # Default checked standard numbered structures automatically to optimize analyst workflows
        chk_box = "[X]" if sec["is_numbered"] else "[ ]"
        
        id_str = f"{sec['index']}".ljust(4)
        lvl_str = f"{sec['level']}".ljust(5)
        
        # Truncate strings nicely to fit clean terminal reporting widths perfectly
        raw_heading = sec['heading']
        if len(raw_heading) > 48:
            raw_heading = raw_heading[:45] + "..."
        heading_padded = raw_heading.ljust(51)
        
        content_padded = sec['content_types']
        
        print(f"| {chk_box}   | {id_str} | {lvl_str} | {heading_padded} | {content_padded}")
        
    print("="*95 + "\n")
    return sections_matrix

# ===========================================================================
# CLI Fallbacks (Unchanged)
# ===========================================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage CLI Option Parameters Missing.")
        sys.exit(0)

    command = sys.argv[1]

    if command == "login":
        do_login()
    elif command == "read":
        if len(sys.argv) < 3:
            print("Usage: python confluence_wiki_reader.py read <page_url>")
            sys.exit(1)
        read_page(sys.argv[2])
    else:
        print(f"Command context not handled inside current scope selector: {command}")
