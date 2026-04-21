"""
Crawl4AI 基础爬虫示例
展示如何使用 AsyncWebCrawler 进行基本的网页爬取和 LLM 提取
"""
import asyncio
import json
import os
import functools
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from flask import Flask, jsonify,request
from colorama import Fore, Style, init
from logger import setup_logger

try:
    logger = setup_logger()
    app = Flask(__name__)
    logger.info(f"{Fore.GREEN}🚀 启动爬虫服务...{Style.RESET_ALL}")
except Exception as e:
    print(f"Error loading .env file: {e}")

def run_async(func):
    """装饰器：同步运行异步函数"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper


class ArticleInfo(BaseModel):
    title: str = Field(..., description="文章标题")
    content: str = Field(..., description="文章的完整内容，保持原文的所有细节和信息，不要删减或总结")
    tags: list[str] = Field(default_factory=list, description="文章标签列表")

async def basic_crawl():
    """最基础的爬虫示例（不使用 LLM）"""
    logger.info("🚀 开始基础爬虫测试...")
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/politics/immigration/immigrant-deaths-custody-grow-ice-reduces-details-are-made-public-rcna331852",
        )
        
        logger.info(f"✅ 爬取成功!")
        logger.info(f"📄 Markdown 长度: {len(result.markdown)} 字符")
        logger.info(f"🔗 提取链接数: {len(result.links.get('internal', []))}")
        logger.info(f"\n📝 前500个字符:\n{result.markdown[:500]}...")

async def llm_extraction(target_url):
    """使用千问 LLM 提取结构化数据，返回统一格式的结果"""
    try:
        load_dotenv('.llm.env')
        api_key = os.getenv('DASHSCOPE_API_KEY')
    except Exception as e:
        logger.error(f"Error loading .llm.env file: {e}")  

    # 初始化返回结构
    result_data = {
        "success": False,
        "url": target_url,
        "extracted_info": "",
        "error": "",
        "scrape_stats": {},
        "model_used": "qwen-plus",
        "tokens_used": 0
    }
    
    if not api_key:
        result_data["error"] = "DASHSCOPE_API_KEY 未设置"
        logger.error(f"❌ {result_data['error']}")
        return result_data
    
    try:
        llm_config = LLMConfig(
            provider="dashscope/qwen-plus", 
            api_token=api_key,
        )
        
        extraction_strategy = LLMExtractionStrategy(
            llm_config=llm_config,
            schema=ArticleInfo.schema(),
            extraction_type="schema",
            instruction="从页面内容中提取文章的完整标题和完整正文内容。要求：1) 标题要准确完整；2) 正文内容要保持原文的所有细节和信息，不要删减、总结或改写，完整保留文章内容；3) 过滤掉广告、导航、页脚等无关内容；4) tags 提取文章的主要话题标签。"
        )
        
        browser_config = BrowserConfig(headless=True, verbose=False)
        run_config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=100
        )
        
        logger.info("🚀 开始使用 Qwen-Plus 提取数据...")
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=target_url,
                config=run_config
            )

        if result.success:
            # 计算抓取统计信息
            content = result.markdown
            total_char_count = len(content)
            total_line_count = content.count("\n") + 1 if content else 0
            
            result_data["success"] = True
            result_data["extracted_info"] = result.extracted_content or ""
            result_data["scrape_stats"] = {
                "line_count": total_line_count,
                "char_count": total_char_count,
                "last_char_line": total_line_count,
                "all_content_displayed": True
            }
            # 注意：Crawl4AI 当前版本可能不直接返回 token 使用量
            # 如果需要精确的 token 统计，可能需要从 LLM 响应中解析
            result_data["tokens_used"] = 0  # 暂时设为 0
            
            logger.info("✅ 提取成功!")
            logger.info(f"📊 内容长度: {total_char_count:,} 字符")
            logger.info(f"📄 行数: {total_line_count:,}")
            logger.info(f"\n提取的结构化数据:")
            logger.info(result_data["extracted_info"])
        else:
            result_data["error"] = f"Scraping failed: {result.error_message}"
            logger.error(f"❌ {result_data['error']}")
            
    except Exception as e:
        result_data["error"] = f"Scraping failed (both Jina and Python): {str(e)}"
        logger.error(f"❌ {result_data['error']}")
        import traceback
        traceback.print_exc()
    
    return result_data

def save_result_to_file(result_data: dict, filename: str = None):
    """将结果保存到 JSON 文件"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"result\crawl_result_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        logger.info(f"\n💾 结果已保存到: {filename}")
        return filename
    except Exception as e:
        logger.error(f"❌ 保存文件失败: {e}")
        return None

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/api/search")
@run_async
async def get_data():
    link= request.args.get("link", "https://www.bbc.com/zhongwen/articles/cx231dzr384o/simp")
    logger.info(link)
    result = await llm_extraction(link)
    return jsonify(result)



if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=False)

