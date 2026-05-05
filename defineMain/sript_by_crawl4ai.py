
from crawl4ai import AsyncWebCrawler, BrowserConfig

from logger import setup_logger
logger = setup_logger()

async def basic_crawl(link: str):
    """最基础的爬虫示例（不使用 LLM）"""
    logger.info("🚀 开始基础爬虫测试...")
    
    browser_config = BrowserConfig(
            headless=False, 
            verbose=False,
            browser_mode='cdp',
            browser_type="chromium",# 指定浏览器内核: "chromium", "firefox", "webkit"
            use_managed_browser=False,
            channel="chrome",
            cdp_url='http://127.0.0.1:9222',
            ignore_https_errors=True, # 忽略 HTTPS 证书错误
            java_script_enabled=True, # 启用 JavaScript
        )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=link,
            )
            
            logger.info(f"✅ 爬取成功!")
            content = result.markdown
            
            # 获取内容统计信息
            total_char_count = len(content)
            total_line_count = content.count("\n") + 1 if content else 0
            
            # 设置显示内容的最大字符数
            max_chars = 40000
            
            # 提取前 max_chars 个字符用于显示
            displayed_content = content[:max_chars]
            all_content_displayed = total_char_count <= max_chars
            
            # 计算最后一个显示字符所在的行号
            if displayed_content:
                last_char_line = displayed_content.count("\n") + 1
            else:
                last_char_line = 0
            
            logger.info(f"📄 Markdown 长度: {total_char_count} 字符")
            logger.info(f"🔗 提取链接数: {len(result.links.get('internal', []))}")
            logger.info(f"📊 行数: {total_line_count}, 全部显示: {all_content_displayed}")
            logger.info(f"\n📝 前500个字符:\n{content[:500]}...")
            
            return {
                "markdown": content,
                "stats": {
                    "line_count": total_line_count,
                    "char_count": total_char_count,
                    "last_char_line": last_char_line,
                    "all_content_displayed": all_content_displayed
                },
                "success": True,
            }
    except Exception as e:
        logger.error(f"爬虫失败: {str(e)}")
        return {
            "markdown": f"爬虫失败: {str(e)}",
            "stats": {
                "line_count": 0,
                "char_count": 0,
                "last_char_line": 0,
                "all_content_displayed": False
            },
            "success": False,
        }
