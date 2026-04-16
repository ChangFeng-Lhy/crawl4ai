"""
Crawl4AI 基础爬虫示例
展示如何使用 AsyncWebCrawler 进行基本的网页爬取
"""
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


async def basic_crawl():
    """最基础的爬虫示例"""
    print("🚀 开始基础爬虫测试...")
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
        )
        
        print(f"✅ 爬取成功!")
        print(f"📄 Markdown 长度: {len(result.markdown)} 字符")
        print(f"🔗 提取链接数: {len(result.links.get('internal', []))}")
        print(f"\n📝 前500个字符:\n{result.markdown[:500]}...")


async def config_crawl():
    """带配置的爬虫示例"""
    print("\n🚀 开始配置爬虫测试...")
    
    # 浏览器配置
    browser_config = BrowserConfig(
        headless=True,  # 无头模式
        verbose=True,   # 详细日志
    )
    
    # 运行配置
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,  # 启用缓存
        word_count_threshold=10,       # 最小词数阈值
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )
        
        print(f"✅ 爬取成功!")
        print(f"📄 Markdown 长度: {len(result.markdown)} 字符")
        print(f"⏱️ 耗时: {result.success}秒")


async def main():
    """主函数"""
    try:
        # 运行基础爬虫
        await basic_crawl()
        
        # 运行配置爬虫
        await config_crawl()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
