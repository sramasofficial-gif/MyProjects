# scripts/confluence_wiki_reader.py
import os
import sys
import asyncio
from playwright.async_api import async_playwright

# Locate a path inside your local script workspace to save authentication state
AUTH_STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth_state.json")

async def read_page_with_sso(target_url: str):
    async with async_playwright() as p:
        # Check if we have an existing authenticated session saved on disk
        has_auth = os.path.exists(AUTH_STATE_PATH)
        
        if not has_auth:
            print("\n" + "="*70)
            print("🔒 [SSO AUTH REQUIRED] No active session file found.")
            print("🚀 Launching a visible browser window so you can log into your company portal.")
            print("👉 Please log in completely, approve MFA/2FA, and wait for the page to load.")
            print("="*70 + "\n")
            
            # 1. Boot up a headed browser window so you can interact with it
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await browser.new_page()
            
            await page.goto(target_url)
            
            # Pause execution and wait in the terminal until you press 'Enter' 
            # after completing the login process in the browser window
            print("\n📝 Press [ENTER] here in the terminal ONLY AFTER you are fully logged in and can see the Confluence wiki content...")
            input()
            
            # Save cookies, local storage tokens, and session variables to a JSON file
            await context.storage_state(path=AUTH_STATE_PATH)
            print(f"✅ Session saved successfully to: {AUTH_STATE_PATH}")
        else:
            # 2. Fast Path: Use the saved session state file to run silently in the background
            print("[🔑] Reusing saved corporate session tokens from storage state...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=AUTH_STATE_PATH)
            page = await browser.new_page()
            await page.goto(target_url)
        
        # --- 📄 EXTRACT DATA FROM THE ARTICLE ---
        # Adjust selector based on your wiki theme layout classes (e.g., #main-content)
        await page.wait_for_selector("div.wiki-content, #main-content", timeout=15000)
        
        # Extract the page content text structure
        article_text = await page.locator("div.wiki-content, #main-content").inner_text()
        
        # Clean up browser threads safely
        await browser.close()
        
        # Print the text to standard output for extraction redirection loops
        print(article_text)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python confluence_wiki_reader.py read <URL>")
        sys.exit(1)
        
    target_link = sys.argv[2]
    asyncio.run(read_page_with_sso(target_link))
