
import os
import asyncio
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig, LLMExtractionStrategy
from pydantic import BaseModel, Field

# 加载环境变量
load_dotenv('.llm.env')


class ArticleInfo(BaseModel):
    """文章信息模型"""
    title: str = Field(..., description="文章标题")
    summary: str = Field(..., description="文章摘要(100字以内)")
    main_topics: list[str] = Field(..., description="主要话题列表")
async def content_filter_example():
    """使用 LLM 进行内容过滤和总结"""
    from crawl4ai.content_filter_strategy import LLMContentFilter
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    
    print("\n\n📝 开始内容过滤测试...")
    
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key or api_key.startswith('YOUR_'):
        print("⚠️  跳过: API Key 未配置")
        return
    
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url="https://www.nbcnews.com/politics/immigration/immigrant-deaths-custody-grow-ice-reduces-details-are-made-public-rcna331852",
                config=CrawlerRunConfig(
                    markdown_generator=DefaultMarkdownGenerator(
                        content_filter=LLMContentFilter(
                            llm_config=LLMConfig(
                                provider="dashscope/qwen-plus",  # 使用较经济的模型
                                api_token=api_key,
                            ),
                            instruction="提取出里面的文章 过滤掉里面不相关的广告或者其他部分 不要修改文章的任何内容"
                        )
                    )
                )
            )
            
            print(f"✅ 过滤成功!")
            print(f"📄 原始 Markdown: {len(result.markdown.raw_markdown)} 字符")
            print(f"🎯 过滤后 Markdown: {len(result.markdown.fit_markdown)} 字符")
            print(f"\n📝 过滤后的前500个字符:\n{result.markdown.fit_markdown[:500]}...")
            with open('example.txt', 'w') as f:
                f.write(result.markdown.fit_markdown)


    except Exception as e:
        print(f"❌ 错误: {e}")


async def main():
    """主函数"""
    print("=" * 60)
    print("Crawl4AI LLM 提取示例")
    print("=" * 60)
    
    # 内容过滤示例
    await content_filter_example()
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
