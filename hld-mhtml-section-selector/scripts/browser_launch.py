import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Launch chromium engine safely (defaults to headless=True behind the scenes)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test loading a lightweight platform reference page
        await page.goto("https://example.com")
        title = await page.title()
        print(f"\n✅ Playwright Sandbox Active! Browser title read successfully: '{title}'")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())