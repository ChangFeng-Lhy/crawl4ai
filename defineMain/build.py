# build_exe.py - Crawl4AI 应用打包脚本
import os
import sys
import subprocess
from pathlib import Path


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
    
    # PyInstaller 命令参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=crawl4ai_app",           # 可执行文件名
        "--onefile",                      # 打包成单个 exe
        # "--windowed",                     # 无控制台窗口（可选，如需调试可去掉）
        "--clean",                        # 清理临时文件
        "--noconfirm",                    # 覆盖已有文件
        
        # 核心依赖模块
        "--hidden-import=crawl4ai",
        "--hidden-import=crawl4ai.async_webcrawler",
        "--hidden-import=crawl4ai.async_crawler_strategy",
        "--hidden-import=crawl4ai.browser_manager",
        "--hidden-import=crawl4ai.types",
        
        # Flask 相关
        "--hidden-import=flask",
        "--hidden-import=jinja2",
        "--hidden-import=werkzeug",
        
        # litellm
        "--hidden-import=litellm",
        "--hidden-import=litellm.litellm_core_utils",
        "--hidden-import=litellm.litellm_core_utils.tokenizers",
        "--hidden-import=litellm.proxy",
        "--hidden-import=litellm.types",
        "--hidden-import=litellm.utils",

        # HTTP 客户端
        "--hidden-import=httpx",
        "--hidden-import=aiohttp",
        
        # 其他必要依赖
        "--hidden-import=pydantic",
        "--hidden-import=beautifulsoup4",
        "--hidden-import=lxml",
        "--hidden-import=colorama",
        "--hidden-import=dotenv",
        "--hidden-import=asyncio",
        
        # 添加数据文件
        f"--add-data={project_root}/defineMain/logger.py;defineMain",
        # 添加 playwright 目录的驱动
        # "--add-data=E:\\code\\ai\\crawl4ai\\.venv\\Lib\\site-packages\\playwright\\driver;playwright/driver",
        "--add-data=E:\\code\\ai\\crawl4ai\\crawl4ai\\js_snippet;crawl4ai/js_snippet",
        "--add-data=E:\\code\\ai\\crawl4ai\\.venv\\Lib\\site-packages\\litellm\\model_prices_and_context_window_backup.json;litellm",
        # 添加 model_prices 文件
        "--add-data=E:\\code\\ai\\crawl4ai\\.venv\\Lib\\site-packages\\litellm\\model_prices_and_context_window_backup.json;litellm",
        # 新增：添加 tokenizers 目录及其所有 json 文件
        "--add-data=E:\\code\\ai\\crawl4ai\\.venv\\Lib\\site-packages\\litellm\\litellm_core_utils\\tokenizers;litellm/litellm_core_utils/tokenizers",
        "--add-data=E:\\code\\ai\\crawl4ai\\.venv\\Lib\\site-packages\\litellm\\containers\\endpoints.json;litellm/containers",

        # 输出目录
        f"--distpath={project_root}/dist",
        f"--workpath={project_root}/build",
        f"--specpath={project_root}",
        
        # 主脚本路径
        str(main_script)
    ]
    
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
        print("1. 运行前请确保目标机器已安装 Chrome 或 Edge 浏览器")
        print("2. 需要手动启动浏览器并开启调试端口:")
        print('   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\temp\\chrome_debug"')
        print("3. 或者修改 main.py 使用 use_managed_browser=True 自动管理浏览器")
        print("4. logs/ 和 result/ 目录会自动创建")
        
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