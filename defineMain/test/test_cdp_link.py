"""
CDP (Chrome DevTools Protocol) 连接测试脚本
用于验证 Playwright 能否成功连接到外部 Chrome 浏览器的调试端口
"""
import asyncio
import sys
from playwright.async_api import async_playwright


async def test_cdp_connection(cdp_url: str = "http://127.0.0.1:9222"):
    """
    测试 CDP 连接
    
    Args:
        cdp_url: Chrome DevTools Protocol 地址
    """
    print(f"🔍 开始测试 CDP 连接: {cdp_url}")
    print("-" * 60)
    
    try:
        # 第一步：检查 Playwright 驱动是否存在
        print("✅ 步骤 1: 检查 Playwright 驱动...")
        try:
            from playwright._impl._driver import compute_driver_executable
            driver_path = compute_driver_executable()
            print(f"   ✓ Playwright 驱动路径: {driver_path}")
        except Exception as e:
            print(f"   ✗ Playwright 驱动检查失败: {e}")
            print("   💡 请运行: python -m playwright install chromium")
            return False
        
        # 第二步：尝试连接 CDP
        print("\n✅ 步骤 2: 尝试连接 CDP...")
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(cdp_url)
                print(f"   ✓ 成功连接到 CDP: {cdp_url}")
                
                # 第三步：获取浏览器信息
                print("\n✅ 步骤 3: 获取浏览器信息...")
                version = await browser.version
                print(f"   ✓ 浏览器版本: {version}")
                
                # 第四步：列出所有上下文
                print("\n✅ 步骤 4: 检查浏览器上下文...")
                contexts = browser.contexts
                print(f"   ✓ 当前上下文数量: {len(contexts)}")
                
                if contexts:
                    for i, context in enumerate(contexts):
                        pages = context.pages
                        print(f"   - 上下文 {i}: {len(pages)} 个页面")
                        for j, page in enumerate(pages):
                            try:
                                title = await page.title()
                                url = page.url
                                print(f"     · 页面 {j}: [{title}] {url}")
                            except:
                                print(f"     · 页面 {j}: <无法获取信息>")
                else:
                    print(" 没有活动的上下文")
                
                # 第五步：创建新页面测试
                print("\n✅ 步骤 5: 创建测试页面...")
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto("https://www.example.com", wait_until="domcontentloaded", timeout=10000)
                title = await page.title()
                print(f"   ✓ 测试页面标题: {title}")
                print(f"   ✓ 测试页面 URL: {page.url}")
                
                # 清理
                await context.close()
                await browser.close()
                
                print("\n" + "=" * 60)
                print("🎉 CDP 连接测试成功！")
                print("=" * 60)
                return True
                
            except Exception as e:
                print(f"   ✗ CDP 连接失败: {e}")
                print("\n可能的原因:")
                print("   1. Chrome 未启动或调试端口未开启")
                print("   2. 端口 9222 被占用或防火墙拦截")
                print("   3. Chrome 启动时未指定 --remote-debugging-port=9222")
                print("   4. Chrome 启动时未指定独立的 --user-data-dir")
                print("\n正确的 Chrome 启动命令示例:")
                print('   chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\chrome-debug-profile"')
                return False
                
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("CDP 连接测试工具")
    print("=" * 60)
    
    # 可以从命令行参数获取 CDP URL
    cdp_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9222"
    
    success = await test_cdp_connection(cdp_url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
