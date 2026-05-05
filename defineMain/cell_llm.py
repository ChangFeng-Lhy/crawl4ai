
import json
import os
from dotenv import load_dotenv
from llm_summary import extract_info_with_llm
from script.sript_by_crawl4ai import basic_crawl
from script.sript_by_python import scrape_url_with_python
from test_jina_scrape import scrape_url_with_jina
from logger import setup_logger

logger = setup_logger()

try:
    load_dotenv('.llm.env')
    SUMMARY_LLM_MODEL_NAME = os.getenv('SUMMARY_LLM_MODEL_NAME')
except Exception as e:
    logger.error(f"Error loading .env file: {e}")


async def cell_llm_summary(link:str,info_to_extract:str,use_jina:bool=False):
    # result_data = {
    #     "success": False,
    #     "url": link,
    #     "extracted_info": "",
    #     "error": "",
    #     "scrape_stats": {},
    #     "model_used": "qwen-plus",
    #     "tokens_used": 0
    # }

    #"stats": 
    #{
    #     "line_count": total_line_count,
    #     "char_count": total_char_count,
    #     "last_char_line": last_char_line,
    #     "all_content_displayed": all_content_displayed
    #},

    crawl_data = {
        "success": False,
    }
    
    basic_result = ""  # 初始化变量
    stats = {}  # 初始化变量

    if not use_jina:
        crawl_data  = await basic_crawl(link)
        # 注意：此时 basic_result 尚未赋值，如果 crawl_data 成功，将在下方分支处理；
        # 如果这里想打印 crawl 的原始结果，应使用 crawl_data 中的字段，或者暂时留空/打印状态
        logger.info(f"crawl4ai and Extract Info: Basic crawl status: {crawl_data.get('success')}")


    if crawl_data["success"] and not use_jina:
        basic_result = crawl_data["markdown"]
        stats = crawl_data["stats"]
    else:
        scrape_result = await scrape_url_with_jina(link, None)
        if not scrape_result["success"]:
            logger.warning(
            f"Jina抓取网页失败: {scrape_result['error']}，尝试使用python的http请求抓取网页信息"
            )
            scrape_result = await scrape_url_with_python(link, None)
            if not scrape_result["success"]:
                logger.error(
                    f"使用python抓取: {scrape_result['error']}"
                )
                return json.dumps(
                    {
                        "success": False,
                        "url": link,
                        "extracted_info": "",
                        "error": f"Scraping failed (both Jina and Python): {scrape_result['error']}",
                        "scrape_stats": {},
                        "tokens_used": 0,
                    },
                    ensure_ascii=False,
                )
            else:
                logger.info(
                    f"Jina Scrape and Extract Info: Python fallback scraping succeeded for URL: {link}"
                )
                stats = {
                    "line_count": scrape_result["line_count"],
                    "char_count": scrape_result["char_count"],
                    "last_char_line": scrape_result["last_char_line"],
                    "all_content_displayed": scrape_result["all_content_displayed"],
                }
                basic_result = scrape_result.get("content", "")  # 从Python抓取结果中获取内容
        else:
            logger.info(
                f"Jina Scrape and Extract Info: Jina scraping succeeded for URL: {link}"
            )
            stats = {
                "line_count": scrape_result.get("line_count", 0),
                "char_count": scrape_result.get("char_count", 0),
                "last_char_line": scrape_result.get("last_char_line", ""),
                "all_content_displayed": scrape_result.get("all_content_displayed", True),
            }
            basic_result = scrape_result.get("content", "")  # 从Jina抓取结果中获取内容


    logger.info(f"info_to_extract: {info_to_extract}")

    llm_result = await extract_info_with_llm(
                            url=link,
                            content=basic_result, 
                            info_to_extract=info_to_extract, 
                            model=SUMMARY_LLM_MODEL_NAME, 
                            max_tokens=8192)
    llm_result["scrape_stats"] = stats
    llm_result["url"] = link
    return llm_result