# Crawl4AI 完整使用指南

> 🚀 **Crawl4AI** 是一个开源的 LLM 友好型网络爬虫和 scraper，专为大语言模型、AI 代理和数据管道设计。

---

## 📋 目录

- [快速开始](#快速开始)
- [安装与配置](#安装与配置)
- [核心使用方法](#核心使用方法)
  - [1. Python SDK](#1-python-sdk)
  - [2. 命令行工具 (CLI)](#2-命令行工具-cli)
  - [3. Docker API](#3-docker-api)
- [高级功能](#高级功能)
  - [内容提取策略](#内容提取策略)
  - [深度爬取](#深度爬取)
  - [自适应爬取](#自适应爬取)
  - [批量处理](#批量处理)
- [浏览器控制](#浏览器控制)
- [实战示例](#实战示例)
- [常见问题](#常见问题)

---

## 快速开始

### 最简单的用法（3行代码）

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)

asyncio.run(main())
```

---

## 安装与配置

### 1. 基础安装

```bash
# 安装最新版本
pip install -U crawl4ai

# 安装预发布版本
pip install crawl4ai --pre

# 运行初始化设置
crawl4ai-setup

# 验证安装
crawl4ai-doctor
```

### 2. 手动安装浏览器

如果遇到浏览器相关问题：

```bash
python -m playwright install --with-deps chromium
```

### 3. 可选依赖

```bash
# 安装所有可选功能
pip install -e ".[all]"

# 仅安装特定功能
pip install -e ".[torch]"           # PyTorch 功能
pip install -e ".[transformer]"     # Transformer 功能
pip install -e ".[sync]"            # 同步版本（已弃用）
```

### 4. Docker 部署

```bash
# 拉取镜像
docker pull unclecode/crawl4ai:latest

# 运行容器
docker run -d -p 11235:11235 --name crawl4ai --shm-size=1g unclecode/crawl4ai:latest

# 访问监控面板
# http://localhost:11235/dashboard
# http://localhost:11235/playground
```

---

## 核心使用方法

### 1. Python SDK

#### 基础用法

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def basic_crawl():
    """基础爬取"""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
        )
        
        # 获取结果
        print(f"标题: {result.metadata.get('title')}")
        print(f"Markdown: {result.markdown[:500]}")
        print(f"HTML: {result.html[:500]}")
        print(f"链接: {result.links}")
        
asyncio.run(basic_crawl())
```

#### 带配置的爬取

```python
async def advanced_crawl():
    """高级爬取配置"""
    
    # 浏览器配置
    browser_config = BrowserConfig(
        headless=True,              # 无头模式
        verbose=True,               # 详细日志
        viewport_width=1920,        # 视口宽度
        viewport_height=1080,       # 视口高度
        user_agent_mode="random",   # 随机 User-Agent
    )
    
    # 爬取配置
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,  # 绕过缓存
        css_selector="#main-content", # CSS 选择器
        word_count_threshold=10,      # 最小词数
        scan_full_page=True,          # 扫描整个页面（滚动）
        delay_before_return_html=2.0, # 返回前等待2秒
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )
        return result
```

#### 会话管理

```python
async def session_crawl():
    """使用会话保持登录状态"""
    
    browser_config = BrowserConfig(
        use_persistent_context=True,
        user_data_dir="/path/to/profile",  # 持久化配置文件路径
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 第一次请求：登录
        result1 = await crawler.arun(
            url="https://example.com/login",
            js_code="""
                document.querySelector('#username').value = 'user';
                document.querySelector('#password').value = 'pass';
                document.querySelector('#login-btn').click();
            """,
        )
        
        # 第二次请求：保持登录状态访问
        result2 = await crawler.arun(
            url="https://example.com/dashboard",
        )
        
        return result2
```

#### JavaScript 执行

```python
async def js_execution():
    """执行 JavaScript 并提取动态内容"""
    
    run_config = CrawlerRunConfig(
        js_code=[
            # 点击加载更多按钮
            "document.querySelector('.load-more').click();",
            # 等待内容加载
            "await new Promise(r => setTimeout(r, 2000));",
            # 滚动到页面底部
            "window.scrollTo(0, document.body.scrollHeight);",
        ],
        wait_for="css:.dynamic-content",  # 等待元素出现
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/infinite-scroll",
            config=run_config
        )
        return result
```

#### 截图和 PDF

```python
async def capture_content():
    """截图和生成 PDF"""
    
    run_config = CrawlerRunConfig(
        screenshot=True,              # 启用截图
        pdf=True,                     # 生成 PDF
        screenshot_wait_for=2.0,      # 截图前等待
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )
        
        # 保存截图
        if result.screenshot:
            with open("screenshot.png", "wb") as f:
                f.write(result.screenshot)
        
        # 保存 PDF
        if result.pdf:
            with open("page.pdf", "wb") as f:
                f.write(result.pdf)
```

---

### 2. 命令行工具 (CLI)

#### 基础用法

```bash
# 简单爬取
crwl https://example.com

# 输出 Markdown
crwl https://example.com -o markdown

# 输出 JSON
crwl https://example.com -o json

# 详细模式
crwl https://example.com -v

# 绕过缓存
crwl https://example.com --bypass-cache
```

#### 高级用法

```bash
# 指定 CSS 选择器
crwl https://example.com -c "css_selector=#main-content"

# 浏览器配置
crwl https://example.com -b "headless=true,viewport_width=1280"

# 深度爬取（BFS 策略，最多10页）
crwl https://docs.crawl4ai.com --deep-crawl bfs --max-pages 10

# 使用配置文件
crwl https://example.com -B browser.yml -C crawler.yml

# 使用浏览器配置文件
crwl https://example.com -p my-profile-name
```

#### LLM 提取

```bash
# 交互式问答
crwl https://example.com -q "这篇文章的主要内容是什么？"

# 结构化数据提取（自动提示配置 LLM）
crwl https://amazon.com/product -j

# 带指令的结构化提取
crwl https://example.com -j "提取所有产品标题和价格"
```

#### 配置文件管理

```bash
# 管理浏览器配置文件
crwl profiles

# 启动 CDP 调试模式
crwl cdp

# 管理内置浏览器
crwl browser start
crwl browser status
crwl browser stop

# 查看全局配置
crwl config list
crwl config set VERBOSE true
```

---

### 3. Docker API

#### REST API 调用

```python
import requests

# 基础爬取
response = requests.post(
    "http://localhost:11235/crawl",
    json={
        "urls": ["https://example.com"],
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True}
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"cache_mode": "bypass"}
        }
    }
)

result = response.json()
print(result)
```

#### Python SDK 客户端

```python
from crawl4ai.docker_client import Crawl4aiDockerClient
from crawl4ai import BrowserConfig, CrawlerRunConfig

async def docker_api_example():
    async with Crawl4aiDockerClient(base_url="http://localhost:11235") as client:
        # 基础爬取
        results = await client.crawl(
            urls=["https://example.com"],
            browser_config=BrowserConfig(headless=True),
            crawler_config=CrawlerRunConfig(cache_mode="bypass")
        )
        
        for result in results:
            print(f"URL: {result.url}")
            print(f"Success: {result.success}")
```

#### 异步任务与 Webhook

```python
# 提交异步任务
response = requests.post(
    "http://localhost:11235/crawl/job",
    json={
        "urls": ["https://example.com"],
        "webhook_config": {
            "webhook_url": "https://your-app.com/webhook",
            "webhook_data_in_payload": True
        }
    }
)

task_id = response.json()["task_id"]
print(f"Task ID: {task_id}")

# 查询任务状态
status = requests.get(f"http://localhost:11235/crawl/job/{task_id}")
print(status.json())
```

---

## 高级功能

### 内容提取策略

#### 1. CSS/XPath 提取

```python
from crawl4ai import JsonCssExtractionStrategy
import json

# 定义提取 schema
schema = {
    "name": "ArticleExtractor",
    "baseSelector": "article.post",
    "fields": [
        {
            "name": "title",
            "selector": "h1.title",
            "type": "text"
        },
        {
            "name": "author",
            "selector": ".author",
            "type": "text"
        },
        {
            "name": "content",
            "selector": ".content",
            "type": "html"
        },
        {
            "name": "publish_date",
            "selector": ".date",
            "type": "attribute",
            "attribute": "datetime"
        }
    ]
}

extraction_strategy = JsonCssExtractionStrategy(schema)

async def css_extraction():
    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://blog.example.com",
            config=run_config
        )
        
        # 解析提取的内容
        data = json.loads(result.extracted_content)
        print(json.dumps(data, indent=2))
```

#### 2. LLM 驱动提取

```python
from crawl4ai import LLMExtractionStrategy, LLMConfig
from pydantic import BaseModel, Field

# 定义数据结构
class Product(BaseModel):
    name: str = Field(..., description="产品名称")
    price: float = Field(..., description="产品价格")
    rating: float = Field(..., description="评分")
    features: list[str] = Field(..., description="产品特性列表")

# 配置 LLM
llm_config = LLMConfig(
    provider="openai/gpt-4o",
    api_token="your-api-key"
)

extraction_strategy = LLMExtractionStrategy(
    llm_config=llm_config,
    schema=Product.schema(),
    extraction_type="schema",
    instruction="从页面中提取所有产品信息"
)

async def llm_extraction():
    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://shop.example.com/products",
            config=run_config
        )
        
        products = json.loads(result.extracted_content)
        for product in products:
            print(f"{product['name']}: ${product['price']}")
```

#### 3. 表格提取

```python
from crawl4ai import DefaultTableExtraction, LLMTableExtraction

# 默认表格提取
table_strategy = DefaultTableExtraction()

# 或使用 LLM 增强版
llm_table_strategy = LLMTableExtraction(
    llm_config=LLMConfig(provider="openai/gpt-4o-mini"),
    enable_chunking=True,
    chunk_token_threshold=5000
)

async def table_extraction():
    run_config = CrawlerRunConfig(
        table_extraction_strategy=llm_table_strategy
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/List_of_countries",
            config=run_config
        )
        
        # 访问提取的表格
        for table in result.tables:
            print(f"表格标题: {table.get('caption')}")
            print(f"表头: {table['headers']}")
            print(f"行数: {len(table['rows'])}")
            
            # 转换为 DataFrame
            import pandas as pd
            df = pd.DataFrame(table['data'])
            print(df.head())
```

#### 4. Markdown 生成优化

```python
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Clean Markdown（清理后的 Markdown）
clean_generator = DefaultMarkdownGenerator()

# Fit Markdown（启发式过滤，去除噪声）
fit_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(
        threshold=0.48,
        threshold_type="fixed",
        min_word_threshold=0
    )
)

# BM25 算法（基于查询的相关性过滤）
bm25_generator = DefaultMarkdownGenerator(
    content_filter=BM25ContentFilter(
        user_query="人工智能技术",
        bm25_threshold=1.0
    )
)

async def markdown_generation():
    run_config = CrawlerRunConfig(
        markdown_generator=fit_generator
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/article",
            config=run_config
        )
        
        print(f"原始 Markdown: {len(result.markdown.raw_markdown)} 字符")
        print(f"精简 Markdown: {len(result.markdown.fit_markdown)} 字符")
```

---

### 深度爬取

#### BFS（广度优先搜索）

```python
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

async def bfs_deep_crawl():
    strategy = BFSDeepCrawlStrategy(
        max_depth=2,        # 最大深度
        max_pages=10,       # 最大页面数
        same_domain=True,   # 仅限同域名
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy
    )
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(
            url="https://docs.example.com",
            config=run_config
        )
        
        for result in results:
            print(f"URL: {result.url}")
            print(f"深度: {result.metadata.get('depth')}")
```

#### DFS（深度优先搜索）

```python
from crawl4ai.deep_crawling import DFSDeepCrawlStrategy

strategy = DFSDeepCrawlStrategy(
    max_depth=3,
    max_pages=20,
)
```

#### Best-First（最佳优先）

```python
from crawl4ai.deep_crawling import BestFirstCrawlStrategy

strategy = BestFirstCrawlStrategy(
    max_depth=2,
    max_pages=15,
    score_threshold=0.5,  # 最低评分阈值
)
```

#### 带过滤的深度爬取

```python
from crawl4ai.deep_crawling import FilterChain, DomainFilter, ContentTypeFilter

strategy = BFSDeepCrawlStrategy(
    max_depth=2,
    max_pages=10,
    filter_chain=FilterChain(
        filters=[
            DomainFilter(allowed_domains=["docs.example.com"]),
            ContentTypeFilter(allowed_types=["text/html"]),
        ]
    )
)
```

---

### 自适应爬取

自适应爬取会根据网站模式自动学习和优化爬取策略。

```python
from crawl4ai import AdaptiveCrawler, AdaptiveConfig

async def adaptive_crawl():
    config = AdaptiveConfig(
        strategy="statistical",  # 或 "embedding"
        confidence_threshold=0.7,  # 置信度阈值
        max_depth=5,               # 最大深度
        max_pages=20,              # 最大页面数
    )
    
    async with AsyncWebCrawler() as crawler:
        adaptive = AdaptiveCrawler(crawler, config)
        
        state = await adaptive.digest(
            start_url="https://news.example.com",
            query="最新科技新闻"
        )
        
        # 查看统计信息
        adaptive.print_stats(detailed=True)
        
        # 获取最相关的内容
        relevant_pages = adaptive.get_relevant_content(top_k=5)
        for page in relevant_pages:
            print(f"URL: {page['url']}")
            print(f"相关性: {page['score']:.2%}")
            print(f"内容预览: {page['content'][:200]}...")
```

---

### 批量处理

#### 基础批量爬取

```python
async def batch_crawl():
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
    ]
    
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler() as crawler:
        # 批量处理（返回所有结果）
        results = await crawler.arun_many(
            urls=urls,
            config=config
        )
        
        for result in results:
            print(f"{result.url}: {len(result.markdown)} 字符")
```

#### 流式批量爬取

```python
async def streaming_batch_crawl():
    urls = ["https://example.com/" + str(i) for i in range(100)]
    
    config = CrawlerRunConfig(
        stream=True,  # 启用流式处理
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler() as crawler:
        # 流式处理（逐个返回结果）
        async for result in await crawler.arun_many(
            urls=urls,
            config=config
        ):
            print(f"处理完成: {result.url}")
            # 可以立即处理每个结果，无需等待全部完成
```

#### 自定义调度器

```python
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher, RateLimiter

async def custom_dispatcher():
    urls = [f"https://example.com/page{i}" for i in range(50)]
    
    # 内存自适应调度器
    dispatcher = MemoryAdaptiveDispatcher(
        max_sessions=8,           # 最大并发会话数
        rate_limiter=RateLimiter(
            base_delay=(1.0, 2.0)  # 请求间隔
        )
    )
    
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=config,
            dispatcher=dispatcher
        )
```

---

## 浏览器控制

### 代理配置

```python
from crawl4ai.async_configs import ProxyConfig

async def proxy_crawl():
    # 单个代理
    proxy_config = ProxyConfig(
        server="http://proxy.example.com:8080",
        username="user",
        password="pass"
    )
    
    browser_config = BrowserConfig(
        proxy_config=proxy_config
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url="https://example.com")
```

### 反机器人检测

```python
async def antibot_crawl():
    """绕过反机器人检测"""
    
    browser_config = BrowserConfig(
        browser_type="undetected",  # 使用防检测浏览器
        extra_args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security"
        ]
    )
    
    run_config = CrawlerRunConfig(
        magic=True,  # 启用魔法模式（自动处理常见反爬措施）
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://protected-site.com",
            config=run_config
        )
```

### 自定义 Hook

```python
async def custom_hooks():
    """使用 Hook 自定义爬取行为"""
    
    # 定义 Hook 函数
    async def on_page_created(page, context, **kwargs):
        """页面创建时执行"""
        # 阻止图片加载以加快速度
        await context.route("**/*.{png,jpg,jpeg,gif}", 
                          lambda route: route.abort())
        return page
    
    async def before_goto(page, context, url, **kwargs):
        """导航前执行"""
        # 添加自定义 headers
        await page.set_extra_http_headers({
            'X-Custom-Header': 'value'
        })
        return page
    
    run_config = CrawlerRunConfig(
        hooks={
            "on_page_context_created": on_page_created,
            "before_goto": before_goto,
        }
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_config
        )
```

---

## 实战示例

### 示例 1：电商产品抓取

```python
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, JsonCssExtractionStrategy

async def scrape_products():
    """抓取电商产品数据"""
    
    # 定义产品提取 schema
    schema = {
        "name": "ProductExtractor",
        "baseSelector": "div.product-card",
        "fields": [
            {"name": "title", "selector": "h2.product-title", "type": "text"},
            {"name": "price", "selector": ".price", "type": "text"},
            {"name": "rating", "selector": ".rating", "type": "text"},
            {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }
    
    extraction_strategy = JsonCssExtractionStrategy(schema)
    
    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        cache_mode="bypass"
    )
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://shop.example.com/products",
            config=run_config
        )
        
        products = json.loads(result.extracted_content)
        
        # 保存到文件
        with open("products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        
        print(f"成功提取 {len(products)} 个产品")
        return products

asyncio.run(scrape_products())
```

### 示例 2：新闻聚合

```python
async def aggregate_news():
    """聚合多个新闻源"""
    
    news_sites = [
        "https://news.ycombinator.com",
        "https://reddit.com/r/technology",
        "https://techcrunch.com",
    ]
    
    config = CrawlerRunConfig(
        css_selector="article, .story, .post",
        word_count_threshold=50,
    )
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=news_sites,
            config=config
        )
        
        all_news = []
        for result in results:
            if result.success:
                all_news.append({
                    "source": result.url,
                    "title": result.metadata.get("title"),
                    "content": result.markdown[:500],
                    "timestamp": result.metadata.get("published_date")
                })
        
        # 保存到文件
        import json
        with open("news_aggregation.json", "w", encoding="utf-8") as f:
            json.dump(all_news, f, ensure_ascii=False, indent=2)
        
        print(f"聚合了 {len(all_news)} 个新闻源")

asyncio.run(aggregate_news())
```

### 示例 3：文档站点完整抓取

```python
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

async def crawl_documentation():
    """完整抓取文档站点"""
    
    strategy = BFSDeepCrawlStrategy(
        max_depth=3,
        max_pages=100,
        same_domain=True,
    )
    
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode="enabled",
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48)
        )
    )
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(
            url="https://docs.python.org/3/",
            config=config
        )
        
        # 保存所有页面
        for i, result in enumerate(results):
            filename = f"docs/page_{i}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result.markdown.fit_markdown)
        
        print(f"成功抓取 {len(results)} 个文档页面")

asyncio.run(crawl_documentation())
```

### 示例 4：带认证的爬取

```python
async def authenticated_crawl():
    """需要登录的站点爬取"""
    
    # 使用持久化配置文件
    browser_config = BrowserConfig(
        use_persistent_context=True,
        user_data_dir="./browser_profile",
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 首次运行：手动登录后保存配置文件
        # 后续运行：直接使用已保存的登录状态
        
        result = await crawler.arun(
            url="https://members-only-site.com/dashboard",
        )
        
        print(f"已登录用户: {result.metadata.get('user')}")
        return result
```

---

## 常见问题

### Q1: 如何处理动态加载的内容？

**A:** 使用 `js_code` 和 `wait_for` 参数：

```python
config = CrawlerRunConfig(
    js_code=[
        "window.scrollTo(0, document.body.scrollHeight);",
        "await new Promise(r => setTimeout(r, 2000));"
    ],
    wait_for="css:.loaded-content",
    delay_before_return_html=3.0
)
```

### Q2: 如何提高爬取速度？

**A:** 
1. 启用缓存：`cache_mode=CacheMode.ENABLED`
2. 使用批量处理：`arun_many()`
3. 增加并发：调整 `max_sessions`
4. 阻止不必要的资源：使用 Hook 阻止图片/CSS

```python
async def block_images(page, context, **kwargs):
    await context.route("**/*.{png,jpg,jpeg,gif,css}", 
                       lambda route: route.abort())
    return page

config = CrawlerRunConfig(
    hooks={"on_page_context_created": block_images}
)
```

### Q3: 如何避免被封禁？

**A:**
1. 使用代理轮换
2. 设置合理的请求间隔
3. 使用随机 User-Agent
4. 启用防检测模式
5. 使用持久化配置文件模拟真实用户

```python
browser_config = BrowserConfig(
    browser_type="undetected",
    user_agent_mode="random",
)

config = CrawlerRunConfig(
    magic=True,
    proxy_config=[ProxyConfig.DIRECT, ProxyConfig(server="...")]
)
```

### Q4: 如何提取特定区域的内容？

**A:** 使用 CSS 选择器：

```python
config = CrawlerRunConfig(
    css_selector="#main-article, article.content, .post-body"
)
```

### Q5: 如何处理 JavaScript 渲染的页面？

**A:** Crawl4AI 默认使用 Playwright，会自动执行 JavaScript。如需额外控制：

```python
config = CrawlerRunConfig(
    js_code="document.querySelector('.load-more').click();",
    wait_for="js:() => document.querySelectorAll('.item').length > 10"
)
```

### Q6: 内存占用过高怎么办？

**A:**
1. 限制并发数：`max_sessions=4`
2. 启用流式处理：`stream=True`
3. 定期清理缓存
4. 使用内存监控

```python
from crawl4ai.memory_utils import MemoryMonitor

monitor = MemoryMonitor()
monitor.start_monitoring()

# 爬取操作...

report = monitor.get_report()
print(f"峰值内存: {report['peak_mb']} MB")
```

### Q7: 如何保存和重用浏览器会话？

**A:** 使用浏览器配置文件：

```bash
# 创建配置文件
crwl profiles

# 使用配置文件
crwl https://example.com -p my-profile
```

或在 Python 中：

```python
browser_config = BrowserConfig(
    use_persistent_context=True,
    user_data_dir="./my_profile"
)
```

---

## 更多资源

- 📖 [官方文档](https://docs.crawl4ai.com/)
- 💬 [Discord 社区](https://discord.gg/jP8KfhDhyN)
- 🐛 [问题反馈](https://github.com/unclecode/crawl4ai/issues)
- ⭐ [GitHub 仓库](https://github.com/unclecode/crawl4ai)

---

## 许可证

本项目采用 Apache License 2.0 许可证。使用时请保留 attribution badge。

---

**Happy Crawling! 🕸️🚀**
