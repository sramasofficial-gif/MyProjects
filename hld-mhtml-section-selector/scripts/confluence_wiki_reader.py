"""
Confluence Wiki Reader - Enterprise Section Extractor & Structural Analyzer
===========================================================================
"""

import sys
import json
import re
import os
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
# scripts/confluence_wiki_reader.py

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
        
        print("[🔒] Validating security tokens and waiting for main layout body...")
        try:
            page.wait_for_selector("[data-testid='content-body'], #main-content, .wiki-content", timeout=25000)
        except Exception as e:
            print("[⚠️] Timeout waiting for explicit Confluence container. Proceeding with fallback scan.")

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
            print("[⚠️] Known content main selector absent. Snapping full body DOM tree.")
            html_content = page.locator("body").inner_html()

        browser.close()

    # -----------------------------------------------------------------------
    # BEAUTIFUL SOUP GRANULAR SECTION PARSER ENGINE
    # -----------------------------------------------------------------------
    soup = BeautifulSoup(html_content, "html.parser")
    for ignore_tag in soup.select(".toc-macro, .confluence-toc, script, style"):
        ignore_tag.extract()

    all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    heading_tags = []
    for h in all_headings:
        if h.find_parent('table') or h.find_parent('th') or h.find_parent('td'):
            continue
        heading_tags.append(h)
    
    sections_matrix = []
    numbered_heading_regex = re.compile(r'^\s*📊?\s*\d+(\.\d+)*')

    for i, heading in enumerate(heading_tags):
        heading_text = heading.get_text().strip()
        if not heading_text:
            continue
            
        is_numbered = bool(numbered_heading_regex.match(heading_text))
        content_fragments = []
        current_node = heading.next_sibling
        
        while current_node and current_node not in heading_tags:
            content_fragments.append(current_node)
            current_node = current_node.next_sibling

        section_html = "".join([str(n) for n in content_fragments])
        section_soup = BeautifulSoup(section_html, "html.parser")
        detected_types = []
        
        if section_soup.find('table') or section_soup.select("table, .pm-table-wrapper"):
            table_count = len(section_soup.select("table")) or 1
            detected_types.append(f"📋 Table ({table_count}x)")
            
        has_image = section_soup.find(['img', 'svg'])
        has_macro_image = section_soup.select(
            ".confluence-embedded-image, .ak-renderer-extension, "
            "[data-macro-name='gliffy'], [data-macro-name='drawio'], "
            "div[class*='fabric-editor'], div[data-viewer='true'], .media-single-container"
        )
        
        if has_image or has_macro_image:
            img_count = len(section_soup.find_all('img')) or len(has_macro_image) or 1
            detected_types.append(f"🖼️ Diagram/Image ({img_count}x)")
            
        if section_soup.find('pre') or section_soup.select(".code, .syntaxhighlighter"):
            detected_types.append("💻 Code Block")
            
        text_payload = section_soup.get_text().strip()
        if len(text_payload) > 15:
            detected_types.append("📝 Text Content")

        if not detected_types:
            detected_types.append("📂 Empty Placeholder")

        sections_matrix.append({
            "index": len(sections_matrix) + 1,
            "heading": heading_text,
            "level": heading.name.upper(),
            "content_types": detected_types,
            "is_numbered": is_numbered
        })

    # -----------------------------------------------------------------------
    # 🟢 FIXED: 100% OFFLINE SELF-CONTAINED ENTERPRISE CLASS VIEW GENERATOR
    # Uses template keyword replacement to fully block python bracket corruption
    # and runs completely offline without relying on external CDN scripts!
    # -----------------------------------------------------------------------
    html_output_path = "hld_specification_review.html"
    table_rows_html = ""
    
    for sec in sections_matrix:
        is_checked = "checked" if sec["is_numbered"] else ""
        row_style_class = "numbered-row" if sec["is_numbered"] else "appendix-row"
        
        pills_html = ""
        for item in sec["content_types"]:
            if "Table" in item:
                pills_html += f'<span class="badge badge-table">{item}</span>'
            elif "Diagram" in item or "Image" in item:
                pills_html += f'<span class="badge badge-diagram">{item}</span>'
            elif "Code" in item:
                pills_html += f'<span class="badge badge-code">{item}</span>'
            elif "Text" in item:
                pills_html += f'<span class="badge badge-text">{item}</span>'
            else:
                pills_html += f'<span class="badge badge-empty">{item}</span>'

        table_rows_html += f"""
        <tr class="{row_style_class}">
            <td style="text-align: center; padding: 12px;"><input type="checkbox" class="section-checkbox" {is_checked}></td>
            <td class="id-cell">{sec['index']}</td>
            <td><span class="badge-level">{sec['level']}</span></td>
            <td class="title-cell">{sec['heading']}</td>
            <td><div class="pill-container">{pills_html}</div></td>
        </tr>
        """

    # Pure standard HTML template block. Notice it uses standard brackets safely
    # because it will be processed via string replacement instead of python f-strings!
    html_template_shell = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enterprise SDLC Blueprint Analyst Matrix</title>
    <style>
        body { font-family: 'Segoe UI', -apple-system, sans-serif; background-color: #f1f5f9; color: #0f172a; padding: 40px; margin: 0; }
        .dashboard-card { background-color: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); max-width: 1200px; margin: 0 auto; overflow: hidden; }
        .card-header { background-color: #111827; color: #ffffff; padding: 24px 32px; }
        .card-header h2 { margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em; }
        .card-header p { margin: 6px 0 0 0; color: #94a3b8; font-size: 13px; font-family: monospace; }
        .toolbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 32px; background-color: #f8fafc; border-bottom: 1px solid #e2e8f0; }
        .stats-bar { font-size: 13px; font-weight: 600; color: #475569; }
        .btn-group { display: flex; gap: 8px; }
        button { background-color: #ffffff; border: 1px solid #cbd5e1; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; color: #334155; transition: all 0.15s ease; }
        button:hover { background-color: #f8fafc; border-color: #0f6cbd; color: #0f6cbd; }
        .table-viewport { max-height: 550px; overflow-y: auto; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }
        thead th { background-color: #f8fafc; position: sticky; top: 0; z-index: 10; padding: 14px 16px; color: #475569; font-weight: 700; border-bottom: 2px solid #e2e8f0; }
        tbody tr { border-bottom: 1px solid #f1f5f9; }
        tbody tr:hover { background-color: #f8fafc; }
        tbody tr.numbered-row { background-color: #ffffff; }
        tbody tr.appendix-row { background-color: #f8fafc; opacity: 0.85; }
        td { padding: 12px 16px; vertical-align: middle; }
        .id-cell { font-family: monospace; font-weight: 700; color: #0f6cbd; }
        .badge-level { background-color: #f1f5f9; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 700; border: 1px solid #cbd5e1; }
        .title-cell { font-weight: 600; color: #1e293b; }
        .pill-container { display: flex; gap: 6px; flex-wrap: wrap; }
        .badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; }
        .badge-table { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
        .badge-diagram { background-color: #f3e8ff; color: #6b21a8; border: 1px solid #e9d5ff; }
        .badge-code { background-color: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
        .badge-text { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .badge-empty { background-color: #f1f5f9; color: #64748b; font-style: italic; font-size: 11px; }
        .section-checkbox { width: 16px; height: 16px; cursor: pointer; accent-color: #0f6cbd; }
    </style>
</head>
<body>
    <div class="dashboard-card">
        <div class="card-header">
            <h2>🎙️ Enterprise SDLC Blueprint Analyst Matrix</h2>
            <p>Target URI: __TARGET_URL_METADATA__</p>
        </div>
        <div class="toolbar">
            <div class="stats-bar">📋 Total Parsed Sections: __TOTAL_SECTIONS_COUNT__</div>
            <div class="btn-group">
                <button onclick="toggleAll(true)">Select All</button>
                <button onclick="toggleAll(false)">Clear All</button>
            </div>
        </div>
        <div class="table-viewport">
            <table>
                <thead>
                    <tr>
                        <th style="text-align: center; width: 60px;">Review</th>
                        <th style="width: 70px;">ID</th>
                        <th style="width: 70px;">Level</th>
                        <th>Section Heading Title Descriptor</th>
                        <th>Detected Content Types Inventory</th>
                    </tr>
                </thead>
                <tbody>
                    __TABLE_ROWS_PLACEHOLDER__
                </tbody>
            </table>
        </div>
    </div>
    <script>
        function toggleAll(status) {
            const checkboxes = document.querySelectorAll('.section-checkbox');
            checkboxes.forEach(cb => cb.checked = status);
        }
    </script>
</body>
</html>
"""

    # 🟢 FIX CORE VULNERABILITY: Perform clean string value mapping substitutions 
    # instead of python f-string operators to completely secure CSS brackets!
    final_output_html = html_template_shell.replace("__TARGET_URL_METADATA__", str(url))
    final_output_html = final_output_html.replace("__TOTAL_SECTIONS_COUNT__", str(len(sections_matrix)))
    final_output_html = final_output_html.replace("__TABLE_ROWS_PLACEHOLDER__", table_rows_html)

    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(final_output_html)
        
    print(f"\n[✔] SUCCESS: Self-contained enterprise matrix written out to workspace.")
    print(f"👉 Path: {os.path.abspath(html_output_path)}\n")
    
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
