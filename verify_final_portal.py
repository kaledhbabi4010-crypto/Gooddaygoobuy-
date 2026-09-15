import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto("file:///app/index.html")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="/home/jules/verification/index_final_screenshot.png", full_page=True)
        await browser.close()
        print("PLAYWRIGHT_FINAL_VERIFIED")

asyncio.run(main())
