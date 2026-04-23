import asyncio
from playwright.async_api import async_playwright

async def test_driver():
    async with async_playwright() as p:
        # 尝试启动一个最小的浏览器实例
        browser = await p.chromium.launch(headless=True)
        print("✅ Playwright 驱动启动成功！")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_driver())