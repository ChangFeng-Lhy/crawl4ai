
import asyncio
import json
import os
from typing import Any, Dict
from dotenv import load_dotenv
import httpx
from logger import setup_logger
from crawl4ai import AsyncWebCrawler, BrowserConfig

logger = setup_logger()
EXTRACT_PROMPT = "提取出里面的文章 过滤掉里面不相关的广告或者其他部分 不要修改文章的任何内容"

EXTRACT_INFO_PROMPT = """You are given a piece of content and the requirement of information to extract. Your task is to extract the information specifically requested. Be precise and focus exclusively on the requested information.

INFORMATION TO EXTRACT:
{}

INSTRUCTIONS:
1. Extract the information relevant to the focus above.
2. If the exact information is not found, extract the most closely related details.
3. Be specific and include exact details when available.
4. Clearly organize the extracted information for easy understanding.
5. Do not include general summaries or unrelated content.

CONTENT TO ANALYZE:
{}

EXTRACTED INFORMATION:"""


try:
    load_dotenv('.llm.env')
    SUMMARY_LLM_MODEL_NAME = os.getenv('SUMMARY_LLM_MODEL_NAME')
    SUMMARY_LLM_BASE_URL = os.getenv('SUMMARY_LLM_BASE_URL')
    SUMMARY_LLM_API_KEY = os.getenv('SUMMARY_LLM_API_KEY')
    if os.getenv('EXTRACT_PROMPT'):
        EXTRACT_PROMPT = os.getenv('EXTRACT_PROMPT')
except Exception as e:
    logger.error(f"Error loading .env file: {e}")


async def basic_crawl(link: str):
    """最基础的爬虫示例（不使用 LLM）"""
    logger.info("🚀 开始基础爬虫测试...")
    
    browser_config = BrowserConfig(
            headless=True, 
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
            
            # 获取内容统计信息（参考 scrape_url_with_jina 的逻辑）
            total_char_count = len(content)
            total_line_count = content.count("\n") + 1 if content else 0
            
            # 设置显示内容的最大字符数（与 LLM 调用的 max_tokens 对应，这里用 40k 作为阈值）
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
                }
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
            }
        }

def get_prompt_with_truncation(
    info_to_extract: str, content: str, truncate_last_num_chars: int = -1
) -> str:
    if truncate_last_num_chars > 0:
        content = content[:-truncate_last_num_chars] + "[...truncated]"

    # Prepare the prompt
    prompt = EXTRACT_INFO_PROMPT.format(info_to_extract, content)
    return prompt

async def extract_info_with_llm(
    url: str,
    content: str,
    info_to_extract: str,
    model: str = "LLM",
    max_tokens: int = 4096,
) -> Dict[str, Any]:
    """
    Summarize content using an LLM API.

    Args:
        content (str): The content to summarize
        info_to_extract (str): The specific types of information to extract (usually a question)
        model (str): The model to use for summarization
        max_tokens (int): Maximum tokens for the response

    Returns:
        Dict[str, Any]: A dictionary containing:
            - success (bool): Whether the operation was successful
            - extracted_info (str): The extracted information
            - error (str): Error message if the operation failed
            - model_used (str): The model used for summarization
            - tokens_used (int): Number of tokens used (if available)
    """

    # Validate input
    if not content or not content.strip():
        return {
            "success": False,
            "extracted_info": "",
            "error": "Content cannot be empty",
            "model_used": model,
            "tokens_used": 0,
        }

    prompt = get_prompt_with_truncation(info_to_extract, content)

    # Prepare the payload
    if "gpt" in model:
        payload = {
            "model": model,
            "max_completion_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }
        # Add cost-saving parameters for GPT-5 models
        if "gpt-5" in model.lower() or "gpt5" in model.lower():
            payload["service_tier"] = "flex"
            payload["reasoning_effort"] = "minimal"
    else:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": 1.0,
            # "top_p": 0.8,
            # "top_k": 20,
        }

    # Validate LLM endpoint configuration early for clearer errors
    if not SUMMARY_LLM_BASE_URL or not SUMMARY_LLM_BASE_URL.strip():
        logger.error("SUMMARY_LLM_BASE_URL环境变量未设置，请检查.env文件")
        return {
            "success": False,
            "extracted_info": "",
            "error": "SUMMARY_LLM_BASE_URL environment variable is not set",
            "model_used": model,
            "tokens_used": 0,
        }

    # Prepare headers (add Authorization if API key is available)
    headers = {"Content-Type": "application/json"}
    if SUMMARY_LLM_API_KEY:
        headers["Authorization"] = f"Bearer {SUMMARY_LLM_API_KEY}"

    try:
        logger.info(f"开始请求用于总结的大模型......")
        
        async with httpx.AsyncClient(trust_env=False) as client:
            response = await client.post(
                SUMMARY_LLM_BASE_URL,
                headers=headers,
                json=payload,
                timeout=httpx.Timeout(None, connect=30, read=300),
            )

        logger.info("请求完成")
        # Check if the request was successful
        if (
            "Requested token count exceeds the model's maximum context length"
            in response.text
            or "longer than the model's context length" in response.text
        ):
            error_msg = "请求的 token 数量超过模型的最大上下文长度"
            logger.error(error_msg)
            return {
                "success": False,
                "extracted_info": "",
                "error": error_msg,
                "model_used": model,
                "tokens_used": 0,
            }

        response.raise_for_status()

    except httpx.ConnectTimeout as e:
        error_msg = f"连接超时: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

    except httpx.ConnectError as e:
        error_msg = f"连接错误: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

    except httpx.ReadTimeout as e:
        error_msg = f"读取超时: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        error_msg = f"HTTP 错误 {status_code}: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

    except httpx.RequestError as e:
        error_msg = f"请求错误: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

    except Exception as e:
        error_msg = f"crawl4ai and Extract Info: Unexpected error during LLM API call: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

    # Parse the response
    try:
        response_data = response.json()

    except json.JSONDecodeError as e:
        error_msg = (
            f"crawl4ai and Extract Info: Failed to parse LLM API response: {str(e)}"
        )
        logger.error(error_msg)
        logger.error(f"Raw response: {response.text}")
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

    # Extract summary from response
    if "choices" in response_data and len(response_data["choices"]) > 0:
        try:
            summary = response_data["choices"][0]["message"]["content"]
        except Exception as e:
            error_msg = f"crawl4ai and Extract Info: Failed to get summary from LLM API response: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "extracted_info": "",
                "error": error_msg,
                "model_used": model,
                "tokens_used": 0,
            }

        # Extract token usage if available
        tokens_used = 0
        if "usage" in response_data:
            tokens_used = response_data["usage"].get("total_tokens", 0)

        return {
            "success": True,
            "extracted_info": summary,
            "error": "",
            "model_used": model,
            "tokens_used": tokens_used,
        }
    elif "error" in response_data:
        error_msg = (
            f"crawl4ai and Extract Info: LLM API error: {response_data['error']}"
        )
        logger.error(error_msg)
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }
    else:
        error_msg = f"crawl4ai and Extract Info: No valid response from LLM API, response data: {response_data}"
        logger.error(error_msg)
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

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

    if info_to_extract == "":
        info_to_extract = EXTRACT_PROMPT

    llm_result = await extract_info_with_llm(
                            url=link,
                            content=basic_result, 
                            info_to_extract=info_to_extract, 
                            model=SUMMARY_LLM_MODEL_NAME, 
                            max_tokens=8192)
    llm_result["scrape_stats"] = crawl_data["stats"]
    llm_result["url"] = link
    return llm_result