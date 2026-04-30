import asyncio
import json
import os
import sys
import functools
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler
from flask import Flask, jsonify,request
from cell_llm import cell_llm_summary
from start_functions import kill_process, setup_playwright_env, start_chrome
from logger import setup_logger


# 设置默认编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# .\chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\temp\chrome-profile"
try:
    logger = setup_logger()
    app = Flask(__name__)
    
    # 配置 Flask 使用 UTF-8 编码
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # 设置响应的字符集为 UTF-8
    @app.after_request
    def set_content_type(response):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
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



@app.route("/")
def hello():
    return "Hello World!"

@app.route("/api/search")
@run_async
async def get_data():
    link= request.args.get("link", "")
    info_to_extract = request.args.get("info_to_extract", "")

    if link == "":
        result_data = {
            "success": False,
            "url": "",
            "extracted_info": "",
            "error": "",
            "scrape_stats": {},
            "model_used": "qwen-plus",
            "tokens_used": 0
        }
        result_data["error"] = "请输入链接"
        return jsonify(result_data)
    logger.info(link)
    start_chrome()
    result = await cell_llm_summary(link=link,info_to_extract=info_to_extract)
    kill_process("chrome.exe")
    return jsonify(result)

if __name__ == "__main__":
    # setup_playwright_env()
    app.run(host="localhost", port=5000, debug=False)

