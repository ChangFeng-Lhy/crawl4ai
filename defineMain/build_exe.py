# build_exe.py - Crawl4AI 应用打包脚本
import os
import sys
import subprocess
from pathlib import Path

def get_playwright_browsers_path():
    """获取 Playwright 浏览器安装路径"""
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        # 获取 Chromium 的执行路径
        browser_type = p.chromium
        # Playwright 浏览器默认安装在用户目录下
        import platform
        if platform.system() == "Windows":
            # Windows 默认路径: C:\Users\用户名\AppData\Local\ms-playwright
            appdata = os.environ.get('LOCALAPPDATA', '')
            browsers_path = os.path.join(appdata, 'ms-playwright')
        else:
            browsers_path = None
        p.stop()
        return browsers_path
    except Exception as e:
        print(f"⚠️  无法获取 Playwright 路径: {e}")
        return None

def build_exe():
    """使用 PyInstaller 打包 Crawl4AI 应用"""
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    main_script = project_root / "defineMain" / "main.py"
    
    if not main_script.exists():
        print(f"❌ 找不到主文件: {main_script}")
        return False
    
    print("🚀 开始打包 Crawl4AI 应用...")
    print(f"📁 项目根目录: {project_root}")
    print(f"📄 主文件: {main_script}")
    
    # 检查并获取 Playwright driver 路径
    print("\n🔍 检查 Playwright driver...")
    try:
        import playwright
        pw_dir = Path(playwright.__file__).parent
        driver_dir = pw_dir / "driver"
        
        if driver_dir.exists():
            print(f"✅ 找到 Playwright driver: {driver_dir}")
            playwright_driver_data = str(driver_dir)
        else:
            print(f"⚠️  警告: Playwright driver 目录不存在: {driver_dir}")
            playwright_driver_data = None
    except ImportError:
        print("⚠️  警告: 无法导入 playwright 模块")
        playwright_driver_data = None
    
    # 检查 Playwright 浏览器是否已安装
    print("\n🔍 检查 Playwright 浏览器...")
    browsers_path = get_playwright_browsers_path()
    if browsers_path and os.path.exists(browsers_path):
        print(f"✅ 找到 Playwright 浏览器目录: {browsers_path}")
    else:
        print("⚠️  警告: 未找到 Playwright 浏览器!")
        print("   请先运行: python -m playwright install chromium")
        response = input("   是否继续打包? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # PyInstaller 命令参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=crawl4ai_app",           # 可执行文件名
        "--onefile",                      # 打包成单个 exe
        "--windowed",                     # 无控制台窗口（可选，如需调试可去掉）
        "--clean",                        # 清理临时文件
        "--noconfirm",                    # 覆盖已有文件
        
        # 添加隐藏导入的模块
        "--hidden-import=crawl4ai",
        "--hidden-import=crawl4ai.async_webcrawler",
        "--hidden-import=crawl4ai.async_crawler_strategy",
        "--hidden-import=crawl4ai.extraction_strategy",
        "--hidden-import=crawl4ai.markdown_generation_strategy",
        "--hidden-import=crawl4ai.content_filter_strategy",
        "--hidden-import=crawl4ai.chunking_strategy",
        "--hidden-import=crawl4ai.models",
        "--hidden-import=crawl4ai.config",
        "--hidden-import=crawl4ai.async_configs",
        "--hidden-import=crawl4ai.browser_manager",
        "--hidden-import=crawl4ai.cache_context",
        "--hidden-import=crawl4ai.async_database",
        "--hidden-import=crawl4ai.html2text",
        "--hidden-import=crawl4ai.js_snippet",
        
        # Playwright 相关
        "--hidden-import=playwright",
        "--hidden-import=playwright.async_api",
        "--hidden-import=playwright.sync_api",
        "--hidden-import=playwright.impl._connection",
        "--hidden-import=playwright.impl._browser_type",
        
        # Flask 相关
        "--hidden-import=flask",
        "--hidden-import=jinja2",
        
        # 其他依赖
        "--hidden-import=pydantic",
        "--hidden-import=aiohttp",
        "--hidden-import=beautifulsoup4",
        "--hidden-import=lxml",
        "--hidden-import=colorama",
        "--hidden-import=dotenv",
        
        # 添加数据文件（如果需要）
        f"--add-data={project_root}/defineMain/logger.py;defineMain",
    ]
    
    # 如果找到 driver 目录，添加到打包数据中
    if playwright_driver_data:
        # Windows 使用分号分隔源和目标路径
        cmd.append(f"--add-data={playwright_driver_data}{os.pathsep}playwright/driver")
        print(f"📦 将包含 Playwright driver: {playwright_driver_data}")
    
    cmd.extend([
        # 输出目录
        f"--distpath={project_root}/dist",
        f"--workpath={project_root}/build",
        f"--specpath={project_root}",
        
        # 主脚本路径
        str(main_script)
    ])
    
    print("\n⚙️  执行命令:")
    print(" ".join(cmd))
    print("\n" + "="*60)
    
    try:
        # 执行打包命令
        result = subprocess.run(cmd, check=True, capture_output=False)
        
        print("\n" + "="*60)
        print("✅ 打包成功!")
        print(f"📦 可执行文件位置: {project_root}/dist/crawl4ai_app.exe")
        print("\n⚠️  重要提示:")
        print("1. 运行前请确保目标机器已安装 Playwright 浏览器:")
        print("   python -m playwright install chromium")
        print("2. 需要 .llm.env 文件放置在 exe 同目录或项目根目录")
        print("3. logs/ 和 result/ 目录会自动创建")
        print("4. 如果目标机器没有安装浏览器,请运行 install_browser.bat")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = build_exe()
    sys.exit(0 if success else 1)