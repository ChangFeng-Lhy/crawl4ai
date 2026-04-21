"""
Jina Scrape - 网页内容提取测试脚本（无交互版本）

此脚本用于直接抓取并提取网页文章内容，自动过滤广告等无关内容。
使用方法:
1. 在脚本顶部配置环境变量和要抓取的URL
2. 运行: uv run python test_jina_scrape.py
"""
import asyncio
import json
from typing import Any, Dict
import httpx
# 请在这里填写您的实际配置

JINA_API_KEY = "jina_1f903d4b0a874c7ca12d1e2764e16c46wDYOn28WoE6QvdZMuBU354vnKtTG"  # Jina API密钥
SUMMARY_LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"  # 千问API地址
SUMMARY_LLM_MODEL_NAME = "qwen-plus"  # 千问模型名称 (qwen-turbo, qwen-plus, qwen-max等)
SUMMARY_LLM_API_KEY = "sk-12211028bd184bef817cb898de4efb9e"  # 千问API密钥
JINA_BASE_URL = "https://r.jina.ai"  # Jina API基础URL(可选)

TARGET_URL = "https://www.nbcnews.com/politics/immigration/immigrant-deaths-custody-grow-ice-reduces-details-are-made-public-rcna331852"

EXTRACT_PROMPT = "提取出里面的文章 过滤掉里面不相关的广告或者其他部分 不要修改文章的任何内容"

async def scrape_url_with_jina(url: str, custom_headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    使用Jina AI抓取网页内容
    Args:
        url: 要抓取的URL
        custom_headers: 自定义请求头
    Returns:
        包含抓取结果的字典
    """
    print(f"\n{'='*80}")
    print(f"🌐 开始抓取网页: {url}")
    print(f"{'='*80}")
    
    if not JINA_API_KEY:
        return {
            "success": False,
            "content": "",
            "error": "JINA_API_KEY未设置",
            "line_count": 0,
            "char_count": 0,
            "last_char_line": 0,
            "all_content_displayed": False,
        }
    
    try:
        # 准备请求头
        headers = {"Authorization": f"Bearer {JINA_API_KEY}"}
        if custom_headers:
            headers.update(custom_headers)
        
        # 构建Jina URL
        jina_url = f"{JINA_BASE_URL}/{url}"
        
        print(f"⏳ 正在通过Jina AI抓取...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                jina_url,
                headers=headers,
                timeout=httpx.Timeout(None, connect=30, read=120),
            )
        
        response.raise_for_status()
        
        content = response.text.strip()
        
        if not content:
            return {
                "success": False,
                "content": "",
                "error": "抓取内容为空",
                "line_count": 0,
                "char_count": 0,
                "last_char_line": 0,
                "all_content_displayed": False,
            }
        
        # 统计信息
        total_char_count = len(content)
        total_line_count = content.count("\n") + 1 if content else 0
        
        print(f"✅ 抓取成功!")
        print(f"📊 内容长度: {total_char_count:,} 字符")
        print(f"📄 行数: {total_line_count:,}")
        
        return {
            "success": True,
            "content": content,
            "error": "",
            "line_count": total_line_count,
            "char_count": total_char_count,
            "last_char_line": total_line_count,
            "all_content_displayed": True,
        }
        
    except Exception as e:
        error_msg = f"抓取失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "content": "",
            "error": error_msg,
            "line_count": 0,
            "char_count": 0,
            "last_char_line": 0,
            "all_content_displayed": False,
        }

async def extract_info_with_llm(
    url: str,
    content: str,
    info_to_extract: str,
    model: str = None,
    max_tokens: int = 8192,
) -> Dict[str, Any]:
    """
    使用LLM从内容中提取指定信息
    
    Args:
        url: 原始URL
        content: 要分析的内容
        info_to_extract: 要提取的信息描述
        model: 使用的模型名称
        max_tokens: 最大token数
    Returns:
        包含提取结果的字典
    """
    if model is None:
        model = SUMMARY_LLM_MODEL_NAME
    
    print(f"\n{'='*80}")
    print(f"🤖 开始LLM信息提取")
    print(f"{'='*80}")
    print(f"📝 提取目标: {info_to_extract}")
    print(f"📊 内容长度: {len(content):,} 字符")
    print(f"🤖 使用模型: {model}")

    # 生成提示词
    prompt = f"""{info_to_extract}

CONTENT TO ANALYZE:
{content}

EXTRACTED INFORMATION:"""
    
    print(f"📝 提示词长度: {len(prompt):,} 字符")

    # 准备请求payload
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    # 准备请求头
    headers = {"Content-Type": "application/json"}
    if SUMMARY_LLM_API_KEY:
        headers["Authorization"] = f"Bearer {SUMMARY_LLM_API_KEY}"

    try:
        # 重试配置
        connect_retry_delays = [1, 2, 4, 8]

        for attempt, delay in enumerate(connect_retry_delays, 1):
            try:
                print(f"⏳ LLM请求尝试 {attempt}/4...")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        SUMMARY_LLM_BASE_URL,
                        headers=headers,
                        json=payload,
                        timeout=httpx.Timeout(None, connect=30, read=300),
                    )

                # 检查响应
                if (
                    "Requested token count exceeds the model's maximum context length"
                    in response.text
                    or "longer than the model's context length" in response.text
                ):
                    print(f"⚠️ Token超出限制,尝试截断内容...")
                    truncated_content = content[:-40960 * attempt] + "[...truncated]"
                    prompt = f"""{info_to_extract}

CONTENT TO ANALYZE:
{truncated_content}

EXTRACTED INFORMATION:"""
                    payload["messages"][0]["content"] = prompt
                    continue

                response.raise_for_status()
                print(f"✅ LLM请求成功! 状态码: {response.status_code}")
                break

            except httpx.ConnectTimeout as e:
                if attempt < len(connect_retry_delays):
                    print(f"⚠️ 连接超时,{delay}秒后重试")
                    await asyncio.sleep(delay)
                    continue
                else:
                    print(f"❌ 连接重试次数用尽")
                    raise e

            except httpx.ReadTimeout as e:
                print(f"⚠️ LLM API读取超时(可能响应较慢)")
                continue

    except Exception as e:
        error_msg = f"LLM调用失败: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

    # 解析响应
    try:
        response_data = response.json()
    except json.JSONDecodeError as e:
        error_msg = f"解析LLM响应失败: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"原始响应: {response.text[:500]}")
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

    # 提取结果
    if "choices" in response_data and len(response_data["choices"]) > 0:
        try:
            summary = response_data["choices"][0]["message"]["content"]
        except Exception as e:
            error_msg = f"从响应中提取内容失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "extracted_info": "",
                "error": error_msg,
                "model_used": model,
                "tokens_used": 0,
            }

        # 提取token使用情况
        tokens_used = 0
        if "usage" in response_data:
            tokens_used = response_data["usage"].get("total_tokens", 0)

        print(f"✅ 信息提取成功!")
        print(f"📊 Token使用: {tokens_used:,}")
        print(f"\n{'='*80}")
        print(f"📄 提取结果:")
        print(f"{'='*80}")
        print(summary)

        return {
            "success": True,
            "extracted_info": summary,
            "error": "",
            "model_used": model,
            "tokens_used": tokens_used,
        }
    elif "error" in response_data:
        error_msg = f"LLM API错误: {response_data['error']}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }
    else:
        error_msg = f"LLM API响应格式异常: {response_data}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "extracted_info": "",
            "error": error_msg,
            "model_used": model,
            "tokens_used": 0,
        }

async def main():
    """主函数"""
    print("\n" + "="*80)
    print("🛠️  Jina Scrape - 网页内容自动提取测试")
    print("="*80)
    
    # 检查必要的配置
    print("\n🔍 检查配置...")
    
    missing_configs = []
    if not JINA_API_KEY:
        missing_configs.append("JINA_API_KEY")
    if not SUMMARY_LLM_BASE_URL:
        missing_configs.append("SUMMARY_LLM_BASE_URL")
    if not SUMMARY_LLM_MODEL_NAME:
        missing_configs.append("SUMMARY_LLM_MODEL_NAME")
    if not SUMMARY_LLM_API_KEY:
        missing_configs.append("SUMMARY_LLM_API_KEY")
    
    if missing_configs:
        print(f"\n❌ 以下配置需要修改: {', '.join(missing_configs)}")
        print("\n请在脚本顶部的'手动配置环境变量'部分填写您的实际配置")
        return
    
    print("✅ 配置检查通过\n")
    
    # 显示配置信息
    print(f"📋 测试配置:")
    print(f"   目标URL: {TARGET_URL}")
    print(f"   提取提示词: {EXTRACT_PROMPT}")
    print(f"   LLM模型: {SUMMARY_LLM_MODEL_NAME}")
    print()
    
    # 步骤1: 抓取网页内容
    print(f"\n{'='*80}")
    print("步骤 1/2: 抓取网页内容")
    print(f"{'='*80}")
    
    scrape_result = await scrape_url_with_jina(TARGET_URL)
    
    if not scrape_result["success"]:
        print(f"\n❌ 网页抓取失败: {scrape_result['error']}")
        return
    
    with open("scraped_content.txt", "w", encoding="utf-8") as f:
        f.write(str(scrape_result))

    # 步骤2: 使用LLM提取文章
    print(f"\n{'='*80}")
    print("步骤 2/2: 使用LLM提取文章内容")
    print(f"{'='*80}")
    
    extracted_result = await extract_info_with_llm(
        url=TARGET_URL,
        content=scrape_result["content"],
        info_to_extract=EXTRACT_PROMPT,
        model=SUMMARY_LLM_MODEL_NAME,
        max_tokens=8192,
    )
    
    # 显示最终结果
    print(f"\n{'='*80}")
    print("📋 测试结果摘要:")
    print(f"{'='*80}")
    print(json.dumps(extracted_result, ensure_ascii=False, indent=2))
    
    if extracted_result["success"]:
        print(f"\n✅ 测试成功完成!")
        print(f"\n💾 提取的文章已显示在上方")
    else:
        print(f"\n❌ 测试失败: {extracted_result['error']}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
