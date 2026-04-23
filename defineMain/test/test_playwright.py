"""
测试 Playwright 驱动及 CDP 连接是否正常
"""
import asyncio
import sys
import os
from playwright.async_api import async_playwright, Error as PlaywrightError

# 添加项目根目录到路径，以便导入 logger (如果需要)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def test_cdp_connection():
    """
    测试是否能通过 CDP 协议连接到本地 Chrome 实例
    """
    cdp_url = 'http://127.0.0.1:9222'
    print(f"🔍 开始测试 CDP 连接: {cdp_url}")
    
    # 1. 检查 Playwright 浏览器驱动是否安装
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # 尝试获取 chromium 执行路径，如果未安装会抛出异常或返回 None
            browser_type = p.chromium
            executable_path = browser_type.executable_path
            if not executable_path or not os.path.exists(executable_path):
                print("❌ 错误: Playwright Chromium 驱动未找到!")
                print("💡 请运行以下命令安装驱动:")
                print("   playwright install chromium")
                return False
            else:
                print(f"✅ Playwright 驱动存在: {executable_path}")
    except Exception as e:
        print(f"❌ 检查驱动时出错: {e}")
        return False

    # 2. 尝试通过 CDP 连接
    try:
        async with async_playwright() as p:
            print(f"⏳ 正在连接 CDP: {cdp_url} ...")
            
            # connect_over_cdp 是专门用于连接已运行浏览器的方法
            browser = await p.chromium.connect_over_cdp(cdp_url)
            
            # 如果连接成功，获取一些基本信息
            version = await browser.version
            context = browser.contexts[0] if browser.contexts else None
            
            print("✅ 连接成功!")
            print(f"📦 浏览器版本: {version}")
            print(f"📂 上下文数量: {len(browser.contexts)}")
            
            # 简单测试：创建一个新页面并关闭，验证控制权
            if context:
                page = await context.new_page()
                await page.goto('about:blank')
                title = await page.title()
                print(f"📄 测试页面标题: '{title}'")
                await page.close()
            
            await browser.close()
            print("🎉 测试完成: 驱动正常，CDP 连接通畅。")
            return True

    except PlaywrightError as e:
        if "Target closed" in str(e) or "Connection refused" in str(e):
            print(f"❌ 连接失败: 无法连接到 {cdp_url}")
            print("💡 可能原因:")
            print("   1. Chrome/Chromium 未启动。")
            print("   2. Chrome 启动时未加参数: --remote-debugging-port=9222")
            print("   3. 端口被防火墙阻止。")
            print("\n💡 启动 Chrome 的命令示例:")
            print(f'   chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\temp\\chrome-profile"')
        else:
            print(f"❌ Playwright 错误: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 在 Windows 上需要设置事件循环策略
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    success = asyncio.run(test_cdp_connection())
    sys.exit(0 if success else 1)