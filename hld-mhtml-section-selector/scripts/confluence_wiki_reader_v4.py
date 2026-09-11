"""
Confluence Wiki Reader + Section Inventory (Entra ID SSO + Passkey auth)
=========================================================================

Adds a `inventory` command to the original login/read/api/search tool:
it walks the ACTUAL rendered page body (not the TOC, which can be
stale or missing) heading-by-heading, waits out Confluence's lazy-load
/ iframe behavior, classifies what each section contains (table,
diagram/image, iframe-diagram, text, or a mix), and produces:
  1. A JSON inventory file (machine-readable)
  2. A self-contained enterprise-style HTML report with checkboxes,
     so you can review/select sections at a glance.

USAGE (new):
    python confluence_wiki_reader.py inventory "<page_url>" [output_prefix]

    -> produces <output_prefix>.json and <output_prefix>.html
       (default prefix: "section_inventory")

    python confluence_wiki_reader.py inventory --demo
    -> generates section_inventory_demo.html from sample data, with
       no login/network needed, so you can preview the report design.

Everything else (login / read / api / search) is unchanged from the
original script.
"""

import sys
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# CONFIGURATION — edit these for your environment
# ---------------------------------------------------------------------------
CONFLUENCE_BASE_URL = "https://reqcentral.com"   # no trailing slash
AUTH_STATE_FILE = "entra_auth_state.json"


# ---------------------------------------------------------------------------
# STEP 1: Interactive login — run this once (and again whenever session expires)
# ---------------------------------------------------------------------------
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
        print(f"\nSession saved to {AUTH_STATE_FILE}. You can now use 'read'/'inventory' commands.")

        browser.close()


# ---------------------------------------------------------------------------
# Shared helper: content container selector, tried newest-UI-first
# ---------------------------------------------------------------------------
CONTENT_SELECTORS = [
    "[data-testid='content-body']",  # Confluence Cloud (newer UI)
    "#main-content",                  # Confluence Server/Data Center, older Cloud
    ".ak-renderer-document",          # Confluence Cloud editor renderer
]


def _find_content_selector(page):
    for selector in CONTENT_SELECTORS:
        if page.locator(selector).count() > 0:
            return selector
    return "body"


# ---------------------------------------------------------------------------
# Helper: force lazy-loaded content (images, iframes, macros) to resolve
# ---------------------------------------------------------------------------
def ensure_full_content_loaded(page, max_scroll_passes=40, settle_ms=600):
    """
    Confluence often renders diagram/macro sections as empty shells until
    they scroll into view (IntersectionObserver) or their iframe finishes
    its own async load. domcontentloaded / networkidle alone is not
    enough. This scrolls the full page in steps, waiting between each,
    then waits for any iframes present to finish loading.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    prev_height = -1
    for _ in range(max_scroll_passes):
        curr_height = page.evaluate("document.body.scrollHeight")
        if curr_height == prev_height:
            break
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(settle_ms)
        prev_height = curr_height

    # scroll back to top (also re-triggers top-of-page lazy sections in some themes)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(settle_ms)

    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    # Give any iframes (draw.io / Gliffy / Visio viewers) a chance to finish
    for frame in page.frames:
        try:
            frame.wait_for_load_state("load", timeout=5000)
        except Exception:
            pass
    page.wait_for_timeout(500)


# ---------------------------------------------------------------------------
# STEP 2: Read a page by scraping rendered HTML (unchanged from original)
# ---------------------------------------------------------------------------
def read_page(url):
    if not Path(AUTH_STATE_FILE).exists():
        print(f"No saved session found ({AUTH_STATE_FILE}). Run 'login' first.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_STATE_FILE)
        page = context.new_page()

        page.goto(url)
        ensure_full_content_loaded(page)

        selector = _find_content_selector(page)
        article_text = page.inner_text(selector)

        browser.close()
        print(article_text)
        return article_text


# ---------------------------------------------------------------------------
# STEP 3 (optional): Read via Confluence REST API (unchanged)
# ---------------------------------------------------------------------------
def read_via_api(page_id):
    if not Path(AUTH_STATE_FILE).exists():
        print(f"No saved session found ({AUTH_STATE_FILE}). Run 'login' first.")
        sys.exit(1)

    with open(AUTH_STATE_FILE, "r") as f:
        state = json.load(f)

    session = requests.Session()
    for cookie in state.get("cookies", []):
        session.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"])

    api_url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}?expand=body.storage"
    resp = session.get(api_url)

    if resp.status_code != 200:
        print(f"API request failed ({resp.status_code}). Falling back to scraping is recommended.")
        print(resp.text[:500])
        sys.exit(1)

    data = resp.json()
    html_body = data["body"]["storage"]["value"]
    text = BeautifulSoup(html_body, "html.parser").get_text(separator="\n").strip()

    print(text)
    return text


# ---------------------------------------------------------------------------
# STEP 4 (helper): Search for a page's ID by title + space key (unchanged)
# ---------------------------------------------------------------------------
def search_page_id(title, space_key):
    if not Path(AUTH_STATE_FILE).exists():
        print(f"No saved session found ({AUTH_STATE_FILE}). Run 'login' first.")
        sys.exit(1)

    with open(AUTH_STATE_FILE, "r") as f:
        state = json.load(f)

    session = requests.Session()
    for cookie in state.get("cookies", []):
        session.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"])

    api_url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
    resp = session.get(api_url, params={"title": title, "spaceKey": space_key})

    if resp.status_code != 200:
        print(f"Search failed ({resp.status_code}).")
        sys.exit(1)

    results = resp.json().get("results", [])
    if not results:
        print("No matching page found.")
        return None

    page_id = results[0]["id"]
    print(f"Found page ID: {page_id}")
    return page_id


# ---------------------------------------------------------------------------
# NEW: Section inventory — walk headings in DOM order, classify content
# ---------------------------------------------------------------------------
# We deliberately do NOT read the TOC macro (it can drift out of sync with
# the actual body). Instead we walk the real rendered body, heading by
# heading, and bucket every content node until the next heading of equal
# or higher level.
SECTION_EXTRACT_JS = r"""
(containerSelector) => {
    const container = document.querySelector(containerSelector) || document.body;

    // Elements we care about, in document order. querySelectorAll already
    // returns document order for a single call like this.
    const relevant = container.querySelectorAll(
        'h1,h2,h3,h4,h5,h6,table,.table-wrap,img,svg,canvas,iframe,' +
        '.confluence-embedded-image,.image-wrap,.confluence-embedded-file-wrapper,' +
        '[class*="drawio" i],[class*="gliffy" i],[class*="diagram" i],' +
        '[data-macro-name],.macro-placeholder,p,ul,ol'
    );

    const sections = [];
    let current = null;
    let preHeadingContent = { types: new Set(), placeholders: 0 };

    const isEmptyShell = (el) => {
        const txt = (el.innerText || '').trim();
        const hasMedia = el.querySelector('img,svg,canvas,iframe');
        return txt.length === 0 && !hasMedia;
    };

    for (const el of relevant) {
        const tag = el.tagName.toLowerCase();

        if (/^h[1-6]$/.test(tag)) {
            if (current) sections.push(current);
            const raw = (el.innerText || '').trim();
            const numMatch = raw.match(/^([0-9]+(\.[0-9]+)*)/);
            current = {
                level: parseInt(tag.slice(1), 10),
                heading: raw,
                numbering: numMatch ? numMatch[1] : null,
                types: new Set(),
                placeholderCount: 0,
                domId: el.id || null
            };
            continue;
        }

        const bucket = current || preHeadingContent;

        // Classification (checked most-specific first)
        if (tag === 'table' || el.classList.contains('table-wrap')) {
            bucket.types.add('table');
        } else if (tag === 'iframe') {
            bucket.types.add('diagram-iframe');
            if (isEmptyShell(el)) bucket.placeholderCount = (bucket.placeholderCount || 0) + 1;
        } else if (tag === 'img' || tag === 'svg' || tag === 'canvas'
                   || el.classList.contains('confluence-embedded-image')
                   || el.classList.contains('image-wrap')) {
            bucket.types.add('image');
        } else if ([...el.classList].some(c => /drawio|gliffy|visio|diagram/i.test(c))) {
            bucket.types.add('diagram');
            if (isEmptyShell(el)) bucket.placeholderCount = (bucket.placeholderCount || 0) + 1;
        } else if (el.classList.contains('macro-placeholder')) {
            bucket.types.add('unresolved-macro');
            bucket.placeholderCount = (bucket.placeholderCount || 0) + 1;
        } else if (el.hasAttribute('data-macro-name')) {
            const macroName = el.getAttribute('data-macro-name') || '';
            if (/gliffy|drawio|visio|diagram/i.test(macroName)) {
                bucket.types.add('diagram');
            } else {
                bucket.types.add('macro:' + macroName);
            }
        } else if (tag === 'p' || tag === 'ul' || tag === 'ol') {
            if ((el.innerText || '').trim().length > 0) bucket.types.add('text');
        }
    }
    if (current) sections.push(current);

    return {
        preHeadingTypes: Array.from(preHeadingContent.types),
        sections: sections.map(s => ({
            level: s.level,
            heading: s.heading,
            numbering: s.numbering,
            types: Array.from(s.types),
            placeholderCount: s.placeholderCount,
            domId: s.domId
        }))
    };
}
"""


def build_inventory(url):
    if not Path(AUTH_STATE_FILE).exists():
        print(f"No saved session found ({AUTH_STATE_FILE}). Run 'login' first.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=AUTH_STATE_FILE)
        page = context.new_page()

        page.goto(url)
        ensure_full_content_loaded(page)

        selector = _find_content_selector(page)
        result = page.evaluate(SECTION_EXTRACT_JS, selector)

        browser.close()
        return result


def _classify_row_status(types, placeholder_count):
    if placeholder_count and placeholder_count > 0:
        return "issue"
    if not types:
        return "empty"
    return "ok"


def run_inventory(url, output_prefix="section_inventory"):
    raw = build_inventory(url)
    sections = raw["sections"]

    rows = []
    for i, s in enumerate(sections):
        rows.append({
            "id": i + 1,
            "level": s["level"],
            "heading": s["heading"],
            "numbering": s["numbering"],
            "types": s["types"],
            "placeholderCount": s["placeholderCount"],
            "status": _classify_row_status(s["types"], s["placeholderCount"]),
        })

    json_path = f"{output_prefix}.json"
    html_path = f"{output_prefix}.html"

    with open(json_path, "w") as f:
        json.dump(rows, f, indent=2)

    html = render_html_report(rows, source_url=url)
    with open(html_path, "w") as f:
        f.write(html)

    print(f"Found {len(rows)} sections.")
    issue_count = sum(1 for r in rows if r["status"] == "issue")
    if issue_count:
        print(f"  {issue_count} section(s) still show empty/placeholder shells — "
              f"re-run if this seems too high, or increase max_scroll_passes/settle_ms.")
    print(f"Wrote {json_path}")
    print(f"Wrote {html_path}  <- open this in a browser")


def run_inventory_demo(output_prefix="section_inventory_demo"):
    demo_rows = [
        {"id": 1, "level": 1, "heading": "1. Overview", "numbering": "1",
         "types": ["text"], "placeholderCount": 0, "status": "ok"},
        {"id": 2, "level": 2, "heading": "2.1 Architecture Summary", "numbering": "2.1",
         "types": ["text", "image"], "placeholderCount": 0, "status": "ok"},
        {"id": 3, "level": 2, "heading": "2.2 Call Flow", "numbering": "2.2",
         "types": ["text"], "placeholderCount": 0, "status": "ok"},
        {"id": 4, "level": 3, "heading": "2.2.1 Retry Matrix", "numbering": "2.2.1",
         "types": ["table"], "placeholderCount": 0, "status": "ok"},
        {"id": 5, "level": 1, "heading": "3. Configuration", "numbering": "3",
         "types": ["table", "text"], "placeholderCount": 0, "status": "ok"},
        {"id": 6, "level": 4, "heading": "29: 1991 - RBCONNECT - ACD", "numbering": "29",
         "types": ["diagram-iframe"], "placeholderCount": 1, "status": "issue"},
        {"id": 7, "level": 1, "heading": "4. Known Issues", "numbering": "4",
         "types": [], "placeholderCount": 0, "status": "empty"},
        {"id": 8, "level": 2, "heading": "4.1 Escalation Contacts", "numbering": "4.1",
         "types": ["table"], "placeholderCount": 0, "status": "ok"},
    ]
    html_path = f"{output_prefix}.html"
    html = render_html_report(demo_rows, source_url="(demo data — no live page read)")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"Wrote {html_path}  <- open this in a browser to preview the report design")


# ---------------------------------------------------------------------------
# Enterprise-style HTML report renderer
# ---------------------------------------------------------------------------
TYPE_LABELS = {
    "table": "Table",
    "image": "Image",
    "diagram": "Diagram",
    "diagram-iframe": "Diagram (iframe)",
    "text": "Text",
    "unresolved-macro": "Unresolved macro",
}


def _type_badge_class(t):
    if t == "table":
        return "badge-table"
    if t in ("diagram", "diagram-iframe"):
        return "badge-diagram"
    if t == "image":
        return "badge-image"
    if t == "unresolved-macro":
        return "badge-issue"
    if t.startswith("macro:"):
        return "badge-macro"
    return "badge-text"


def render_html_report(rows, source_url=""):
    data_json = json.dumps(rows)

    body_rows_js = "/* rendered client-side from DATA */"

    type_label_json = json.dumps(TYPE_LABELS)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Section Inventory</title>
<style>
  :root {
    --ink: #16212e;
    --ink-soft: #4a5a6b;
    --line: #d9e0e7;
    --panel: #ffffff;
    --bg: #eef1f4;
    --accent: #2a5b8c;
    --accent-soft: #e4edf6;
    --ok: #2f7d4f;
    --ok-bg: #e5f3ea;
    --issue: #b4570a;
    --issue-bg: #fbead9;
    --empty: #8a94a0;
    --empty-bg: #eef0f2;
    --mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    --sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: var(--sans);
    font-size: 14px;
    line-height: 1.5;
    padding: 28px 20px 90px;
  }
  .wrap { max-width: 1080px; margin: 0 auto; }

  header.page-head {
    margin-bottom: 18px;
  }
  header.page-head h1 {
    font-size: 20px;
    font-weight: 650;
    margin: 0 0 4px;
    letter-spacing: -0.01em;
  }
  header.page-head .source {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--ink-soft);
    word-break: break-all;
  }

  .stat-bar {
    display: flex;
    gap: 10px;
    margin: 16px 0 18px;
    flex-wrap: wrap;
  }
  .stat {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 10px 14px;
    min-width: 108px;
  }
  .stat .num { font-size: 20px; font-weight: 650; }
  .stat .label { font-size: 11.5px; color: var(--ink-soft); margin-top: 2px; }
  .stat.issue .num { color: var(--issue); }
  .stat.ok .num { color: var(--ok); }

  .toolbar {
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 12px;
    flex-wrap: wrap;
  }
  .toolbar input[type="search"] {
    flex: 1;
    min-width: 180px;
    padding: 8px 10px;
    border: 1px solid var(--line);
    border-radius: 6px;
    font-size: 13.5px;
    background: var(--panel);
  }
  .toolbar select {
    padding: 8px 10px;
    border: 1px solid var(--line);
    border-radius: 6px;
    font-size: 13.5px;
    background: var(--panel);
  }

  table.inv {
    width: 100%;
    border-collapse: collapse;
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
  }
  table.inv thead th {
    position: sticky;
    top: 0;
    background: #f6f8fa;
    border-bottom: 1px solid var(--line);
    text-align: left;
    font-size: 11.5px;
    font-weight: 650;
    color: var(--ink-soft);
    padding: 10px 12px;
    white-space: nowrap;
  }
  table.inv tbody td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--line);
    vertical-align: top;
  }
  table.inv tbody tr:last-child td { border-bottom: none; }
  table.inv tbody tr:hover { background: #fafbfc; }
  table.inv tbody tr.row-issue { background: var(--issue-bg); }
  table.inv tbody tr.row-issue:hover { background: #f7e0c4; }
  table.inv tbody tr.selected { outline: 2px solid var(--accent); outline-offset: -2px; }

  td.col-check { width: 34px; }
  td.col-id { width: 40px; font-family: var(--mono); color: var(--ink-soft); }
  td.col-num { width: 76px; font-family: var(--mono); color: var(--ink-soft); }
  td.col-status { width: 96px; }

  .heading-cell { display: flex; align-items: baseline; gap: 6px; }
  .heading-text { font-weight: 500; }
  .lvl-1 .heading-text { font-weight: 650; }
  .lvl-2 { padding-left: 14px; }
  .lvl-3 { padding-left: 28px; }
  .lvl-4 { padding-left: 42px; }
  .lvl-5 { padding-left: 56px; }
  .lvl-6 { padding-left: 70px; }

  .badges { display: flex; flex-wrap: wrap; gap: 5px; }
  .badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 100px;
    white-space: nowrap;
  }
  .badge-table { background: var(--accent-soft); color: var(--accent); }
  .badge-diagram { background: #efe6f7; color: #6b3fa0; }
  .badge-image { background: #e7f4ee; color: #227a52; }
  .badge-text { background: var(--empty-bg); color: var(--ink-soft); }
  .badge-macro { background: #fdf3d8; color: #96700a; }
  .badge-issue { background: var(--issue-bg); color: var(--issue); }

  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11.5px;
    font-weight: 600;
    padding: 3px 9px;
    border-radius: 100px;
  }
  .status-ok { background: var(--ok-bg); color: var(--ok); }
  .status-issue { background: var(--issue-bg); color: var(--issue); }
  .status-empty { background: var(--empty-bg); color: var(--empty); }
  .status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

  .selection-bar {
    position: fixed;
    left: 0; right: 0; bottom: 0;
    background: var(--ink);
    color: #fff;
    padding: 12px 20px;
    display: none;
    align-items: center;
    gap: 14px;
    font-size: 13.5px;
    box-shadow: 0 -4px 16px rgba(0,0,0,0.15);
  }
  .selection-bar.visible { display: flex; }
  .selection-bar .count { font-weight: 650; }
  .selection-bar button {
    margin-left: auto;
    background: #fff;
    color: var(--ink);
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 650;
    cursor: pointer;
  }
  .selection-bar button:hover { background: #e9edf1; }
  .selection-bar .clear-btn {
    background: transparent;
    color: #cfd8e0;
    margin-left: 0;
    text-decoration: underline;
    padding: 8px 4px;
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
    color: var(--ink-soft);
    font-size: 13.5px;
  }

  @media (max-width: 640px) {
    body { padding: 16px 10px 90px; }
    table.inv thead { display: none; }
    table.inv, table.inv tbody, table.inv tr, table.inv td { display: block; width: 100%; }
    table.inv tbody tr { border-bottom: 6px solid var(--bg); padding: 10px 4px; }
    table.inv tbody td { border-bottom: none; padding: 4px 8px; }
    td.col-check { display: inline-block; width: auto; }
    td.col-id { display: inline-block; width: auto; }
    .heading-cell { padding-left: 0 !important; }
  }
</style>
</head>
<body>
<div class="wrap">
  <header class="page-head">
    <h1>Section Inventory</h1>
    <div class="source">__SOURCE_URL__</div>
  </header>

  <div class="stat-bar" id="statBar"></div>

  <div class="toolbar">
    <input type="search" id="searchBox" placeholder="Filter by heading text\u2026">
    <select id="typeFilter">
      <option value="">All content types</option>
    </select>
    <select id="statusFilter">
      <option value="">All statuses</option>
      <option value="ok">OK</option>
      <option value="issue">Possible issue</option>
      <option value="empty">Empty</option>
    </select>
  </div>

  <table class="inv" id="invTable">
    <thead>
      <tr>
        <th class="col-check"><input type="checkbox" id="selectAll"></th>
        <th class="col-id">#</th>
        <th class="col-num">No.</th>
        <th>Section Heading</th>
        <th>Content Type(s)</th>
        <th class="col-status">Status</th>
      </tr>
    </thead>
    <tbody id="invBody"></tbody>
  </table>
  <div class="empty-state" id="emptyState" style="display:none;">No sections match the current filter.</div>
</div>

<div class="selection-bar" id="selectionBar">
  <span class="count"><span id="selCount">0</span> selected</span>
  <button class="clear-btn" id="clearSelBtn">Clear</button>
  <button id="copySelBtn">Copy selected headings</button>
</div>

<script>
const DATA = __DATA_JSON__;
const TYPE_LABELS = __TYPE_LABEL_JSON__;

const selected = new Set();

function badgeClass(t) {
  if (t === 'table') return 'badge-table';
  if (t === 'diagram' || t === 'diagram-iframe') return 'badge-diagram';
  if (t === 'image') return 'badge-image';
  if (t === 'unresolved-macro') return 'badge-issue';
  if (t.startsWith('macro:')) return 'badge-macro';
  return 'badge-text';
}

function typeLabel(t) {
  return TYPE_LABELS[t] || (t.startsWith('macro:') ? t.slice(6) : t);
}

function renderStats() {
  const total = DATA.length;
  const withTable = DATA.filter(r => r.types.includes('table')).length;
  const withDiagram = DATA.filter(r => r.types.includes('diagram') || r.types.includes('diagram-iframe')).length;
  const issues = DATA.filter(r => r.status === 'issue').length;
  const stats = [
    { label: 'Total sections', value: total, cls: '' },
    { label: 'With tables', value: withTable, cls: '' },
    { label: 'With diagrams', value: withDiagram, cls: '' },
    { label: 'Possible issues', value: issues, cls: issues ? 'issue' : 'ok' },
  ];
  document.getElementById('statBar').innerHTML = stats.map(s =>
    `<div class="stat ${s.cls}"><div class="num">${s.value}</div><div class="label">${s.label}</div></div>`
  ).join('');
}

function populateTypeFilter() {
  const allTypes = new Set();
  DATA.forEach(r => r.types.forEach(t => allTypes.add(t)));
  const sel = document.getElementById('typeFilter');
  Array.from(allTypes).sort().forEach(t => {
    const opt = document.createElement('option');
    opt.value = t;
    opt.textContent = typeLabel(t);
    sel.appendChild(opt);
  });
}

function statusPill(status) {
  const map = {
    ok: ['status-ok', 'OK'],
    issue: ['status-issue', 'Check'],
    empty: ['status-empty', 'Empty'],
  };
  const [cls, label] = map[status] || map.ok;
  return `<span class="status-pill ${cls}"><span class="status-dot"></span>${label}</span>`;
}

function currentFilters() {
  return {
    q: document.getElementById('searchBox').value.trim().toLowerCase(),
    type: document.getElementById('typeFilter').value,
    status: document.getElementById('statusFilter').value,
  };
}

function renderRows() {
  const { q, type, status } = currentFilters();
  const tbody = document.getElementById('invBody');
  const filtered = DATA.filter(r => {
    if (q && !r.heading.toLowerCase().includes(q)) return false;
    if (type && !r.types.includes(type)) return false;
    if (status && r.status !== status) return false;
    return true;
  });

  document.getElementById('emptyState').style.display = filtered.length ? 'none' : 'block';

  tbody.innerHTML = filtered.map(r => {
    const badges = r.types.length
      ? r.types.map(t => `<span class="badge ${badgeClass(t)}">${typeLabel(t)}</span>`).join('')
      : `<span class="badge badge-text">None detected</span>`;
    const rowClass = r.status === 'issue' ? 'row-issue' : '';
    const isSel = selected.has(r.id) ? 'selected' : '';
    return `<tr class="${rowClass} ${isSel}" data-id="${r.id}">
      <td class="col-check"><input type="checkbox" class="rowCheck" data-id="${r.id}" ${selected.has(r.id) ? 'checked' : ''}></td>
      <td class="col-id">${r.id}</td>
      <td class="col-num">${r.numbering || '\u2014'}</td>
      <td class="heading-cell lvl-${r.level}"><span class="heading-text">${r.heading}</span></td>
      <td><div class="badges">${badges}</div></td>
      <td class="col-status">${statusPill(r.status)}</td>
    </tr>`;
  }).join('');

  document.querySelectorAll('.rowCheck').forEach(cb => {
    cb.addEventListener('change', (e) => {
      const id = parseInt(e.target.getAttribute('data-id'), 10);
      if (e.target.checked) selected.add(id); else selected.delete(id);
      e.target.closest('tr').classList.toggle('selected', e.target.checked);
      renderSelectionBar();
    });
  });
}

function renderSelectionBar() {
  const bar = document.getElementById('selectionBar');
  const count = selected.size;
  document.getElementById('selCount').textContent = count;
  bar.classList.toggle('visible', count > 0);
}

document.getElementById('selectAll').addEventListener('change', (e) => {
  const { q, type, status } = currentFilters();
  const visibleIds = DATA.filter(r => {
    if (q && !r.heading.toLowerCase().includes(q)) return false;
    if (type && !r.types.includes(type)) return false;
    if (status && r.status !== status) return false;
    return true;
  }).map(r => r.id);
  if (e.target.checked) visibleIds.forEach(id => selected.add(id));
  else visibleIds.forEach(id => selected.delete(id));
  renderRows();
  renderSelectionBar();
});

document.getElementById('clearSelBtn').addEventListener('click', () => {
  selected.clear();
  renderRows();
  renderSelectionBar();
});

document.getElementById('copySelBtn').addEventListener('click', () => {
  const chosen = DATA.filter(r => selected.has(r.id));
  const text = chosen.map(r => `${r.numbering ? r.numbering + ' ' : ''}${r.heading}`).join('\n');
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById('copySelBtn');
    const original = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = original; }, 1200);
  });
});

document.getElementById('searchBox').addEventListener('input', renderRows);
document.getElementById('typeFilter').addEventListener('change', renderRows);
document.getElementById('statusFilter').addEventListener('change', renderRows);

renderStats();
populateTypeFilter();
renderRows();
renderSelectionBar();
</script>
</body>
</html>
"""
    html = html.replace("__SOURCE_URL__", source_url)
    html = html.replace("__DATA_JSON__", data_json)
    html = html.replace("__TYPE_LABEL_JSON__", type_label_json)
    return html


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]

    if command == "login":
        do_login()

    elif command == "read":
        if len(sys.argv) < 3:
            print("Usage: python confluence_wiki_reader.py read <page_url>")
            sys.exit(1)
        read_page(sys.argv[2])

    elif command == "api":
        if len(sys.argv) < 3:
            print("Usage: python confluence_wiki_reader.py api <page_id>")
            sys.exit(1)
        read_via_api(sys.argv[2])

    elif command == "search":
        if len(sys.argv) < 4:
            print("Usage: python confluence_wiki_reader.py search <title> <space_key>")
            sys.exit(1)
        search_page_id(sys.argv[2], sys.argv[3])

    elif command == "inventory":
        if len(sys.argv) >= 3 and sys.argv[2] == "--demo":
            run_inventory_demo()
        elif len(sys.argv) >= 3:
            prefix = sys.argv[3] if len(sys.argv) >= 4 else "section_inventory"
            run_inventory(sys.argv[2], prefix)
        else:
            print("Usage: python confluence_wiki_reader.py inventory <page_url> [output_prefix]")
            print("   or: python confluence_wiki_reader.py inventory --demo")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)