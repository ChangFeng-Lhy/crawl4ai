
import os
from dotenv import load_dotenv
from defineMain.llm_summary import extract_info_with_llm
from sript_by_crawl4ai import basic_crawl
from logger import setup_logger

logger = setup_logger()

try:
    load_dotenv('.llm.env')
    SUMMARY_LLM_MODEL_NAME = os.getenv('SUMMARY_LLM_MODEL_NAME')
except Exception as e:
    logger.error(f"Error loading .env file: {e}")


async def cell_llm_summary(link:str,info_to_extract:str):
    # result_data = {
    #     "success": False,
    #     "url": link,
    #     "extracted_info": "",
    #     "error": "",
    #     "scrape_stats": {},
    #     "model_used": "qwen-plus",
    #     "tokens_used": 0
    # }
    
    crawl_data  = await basic_crawl(link)

    basic_result = crawl_data["markdown"]
    logger.info(f"crawl4ai and Extract Info: Basic crawl result: {basic_result[:500]}")
    logger.info(f"info_to_extract: {info_to_extract}")


    llm_result = await extract_info_with_llm(
                            url=link,
                            content=basic_result, 
                            info_to_extract=info_to_extract, 
                            model=SUMMARY_LLM_MODEL_NAME, 
                            max_tokens=8192)
    llm_result["scrape_stats"] = crawl_data["stats"]
    llm_result["url"] = link
    return llm_result