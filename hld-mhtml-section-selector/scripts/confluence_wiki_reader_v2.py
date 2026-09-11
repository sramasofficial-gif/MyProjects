"""
Confluence Wiki Reader (Entra ID SSO + Passkey auth)
=====================================================

PURPOSE:
Access a customer's Confluence wiki that sits behind Entra ID SSO
(with passkey/MFA on your phone), by logging in interactively ONCE,
saving the browser session, then reusing that session headlessly for
all future reads — no repeated login/passkey prompts until the
session expires.

REQUIREMENTS (run once):
    pip install playwright requests beautifulsoup4
    playwright install chromium 
    In Windows Powershell (if there is a error in above install):
        $env:NODE_TLS_REJECT_UNAUTHORIZED="0"; playwright install chromium

USAGE:
    Step 1: python confluence_wiki_reader.py login
            -> opens a real browser window, you log in manually
               (Entra ID username/password + passkey approval on phone)
            -> press Enter in the terminal once you're logged in and
               can see the wiki/Outlook etc. working
            -> session is saved to entra_auth_state.json

    Step 2: python confluence_wiki_reader.py read "<page_url>"
            -> loads the saved session headlessly and prints the
               page's text content

               Example:
               Run following in PowerShell :
               
               $PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
               python -X utf8 confluence_wiki_reader.py read "https://reqcentral.com/wiki/spaces/FES/pages/1143493583/High+Level+Design+Document+-+Contact+Center+-+BAU+R12.0#HighLevelDesignDocumentContactCenterBAUR12.0-2.6.2DataLifecycleandRetention" | Out-File -Encoding utf8 HLD.txt


    Step 3 (optional, faster/cleaner): python confluence_wiki_reader.py api <page_id>
            -> tries the Confluence REST API using the saved cookies
               instead of scraping rendered HTML

NOTES:
- You must be on the required company/customer network (VPN if
  applicable) for both login and subsequent reads, if Conditional
  Access enforces network location.
- Session lifetime depends on the customer's Entra ID Conditional
  Access policy. When it expires, just re-run the "login" step.
- Adjust CONFLUENCE_BASE_URL below to your customer's wiki domain.
"""


import sys
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# CONFIGURATION — edit these for your environment
# ---------------------------------------------------------------------------
# URL is https://reqcentral.com/wiki/spaces/FES/pages/1143493583/High+Level+Design+Document+-+Contact+Center+-+BAU+R12.0#HighLevelDesignDocumentContactCenterBAUR12.0-2.6.2DataLifecycleandRetention

# CONFLUENCE_BASE_URL = "https://wiki.customer-site.com"   # no trailing slash
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
        print(f"\nSession saved to {AUTH_STATE_FILE}. You can now use 'read' or 'api' commands.")

        browser.close()


# ---------------------------------------------------------------------------
# STEP 2: Read a page by scraping rendered HTML (works regardless of API access)
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
        page.wait_for_load_state("networkidle")

        # Try common Confluence content selectors, newest UI first
        selectors_to_try = [
            "[data-testid='content-body']",  # Confluence Cloud (newer UI)
            "#main-content",                  # Confluence Server/Data Center, older Cloud
            ".ak-renderer-document",          # Confluence Cloud editor renderer
        ]

        article_text = None
        for selector in selectors_to_try:
            if page.locator(selector).count() > 0:
                article_text = page.inner_text(selector)
                break

        if article_text is None:
            print("Could not find a known content selector — dumping full page text instead.")
            article_text = page.inner_text("body")

        browser.close()

        print(article_text)
        return article_text


# ---------------------------------------------------------------------------
# STEP 3 (optional): Read via Confluence REST API using saved session cookies
# ---------------------------------------------------------------------------
def read_via_api(page_id):
    if not Path(AUTH_STATE_FILE).exists():
        print(f"No saved session found ({AUTH_STATE_FILE}). Run 'login' first.")
        sys.exit(1)

    # Load cookies from the saved Playwright storage state
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
# STEP 4 (helper): Search for a page's ID by title + space key
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

    else:
        print(f"Unknown command: {command}")
        print(__doc__)