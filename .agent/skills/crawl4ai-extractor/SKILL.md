---
name: crawl4ai-extractor
description: Extract clean, LLM-native content from web pages using Crawl4AI. Specialized for Arabic e-commerce sites (Salla, Zid). Output structured Markdown free of navigation/footer noise. Use when scraping product pages, extracting content for analysis, or gathering data for AEO audits.
---

# Crawl4AI Extractor

Extract clean, structured content from Arabic e-commerce sites using Crawl4AI.

## Basic Usage

Crawl4AI provides LLM-native Markdown output:

```python
from crawl4ai import AsyncWebCrawler

async def extract_product_page(url: str):
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            word_count_threshold=10,  # Filter out short noise
            exclude_external_links=True,
            exclude_social_media_links=True,
        )
        
        return {
            "markdown": result.markdown,
            "html": result.html,
            "links": result.links,
            "media": result.media
        }
```

## Arabic E-commerce Optimizations

### Salla Platform Detection

```python
def detect_platform(url: str, html: str) -> str:
    """Detect e-commerce platform"""
    
    if "salla.sa" in url or "cdn.salla.network" in html:
        return "salla"
    elif "zid.sa" in url or "cdn.zid.dev" in html:
        return "zid"
    elif "shopify" in html:
        return "shopify"
    else:
        return "unknown"
```

### LLM Extraction Strategy

Use Crawl4AI's LLM extraction for structured data:

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import json

async def extract_product_structured(url: str):
    """Extract product data using LLM strategy"""
    
    schema = {
        "name": "Product",
        "baseSelector": "body",
        "fields": [
            {"name": "title", "type": "string"},
            {"name": "price", "type": "string"},
            {"name": "currency", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "availability", "type": "string"},
            {"name": "images", "type": "array"},
            {"name": "sku", "type": "string"}
        ]
    }
    
    extraction_strategy = LLMExtractionStrategy(
        provider="ollama/llama3",  # Use local Ollama
        schema=schema,
        instruction="Extract product information from this Arabic e-commerce page"
    )
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            extraction_strategy=extraction_strategy
        )
        
        return json.loads(result.extracted_content)
```

## Noise Filtering

Remove navigation, footers, and irrelevant content:

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.chunking_strategy import RegexChunking

async def extract_clean_content(url: str):
    """Extract only main content, filter noise"""
    
    # CSS selectors to exclude
    excluded_tags = [
        'nav', 'header', 'footer', 
        '.navigation', '.menu', '.sidebar',
        '.cookie-notice', '.popup'
    ]
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            excluded_tags=excluded_tags,
            word_count_threshold=15,  # Skip short blocks
            remove_overlay_elements=True
        )
        
        return {
            "clean_markdown": result.markdown,
            "main_content": result.fit_markdown  # Filtered for relevance
        }
```

## Bilingual Page Handling

Extract both Arabic and English versions:

```python
async def extract_bilingual(base_url: str):
    """Extract both language versions"""
    
    # Detect URL patterns
    ar_url = base_url if "/ar" in base_url else f"{base_url}/ar"
    en_url = base_url.replace("/ar", "/en") if "/ar" in base_url else f"{base_url}/en"
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Concurrent extraction
        ar_result = await crawler.arun(ar_url)
        en_result = await crawler.arun(en_url)
        
        return {
            "arabic": {
                "url": ar_url,
                "content": ar_result.markdown,
                "html": ar_result.html
            },
            "english": {
                "url": en_url,
                "content": en_result.markdown,
                "html": en_result.html
            }
        }
```

## JSON-LD Extraction

Extract structured data from pages:

```python
async def extract_jsonld(url: str):
    """Extract JSON-LD schema from page"""
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url)
        
        # Parse JSON-LD from HTML
        from bs4 import BeautifulSoup
        import json
        
        soup = BeautifulSoup(result.html, 'html.parser')
        scripts = soup.find_all('script', type='application/ld+json')
        
        jsonld_data = []
        for script in scripts:
            try:
                data = json.loads(script.string)
                jsonld_data.append(data)
            except:
                pass
        
        return {
            "markdown": result.markdown,
            "jsonld": jsonld_data
        }
```

## Media Extraction

Extract product images and videos:

```python
async def extract_media(url: str):
    """Extract images and videos from product page"""
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            screenshot=True  # Optionally capture screenshot
        )
        
        # Filter for product images (exclude icons, logos)
        product_images = [
            img for img in result.media.get("images", [])
            if not any(x in img["src"].lower() for x in ["logo", "icon", "favicon"])
        ]
        
        return {
            "images": product_images,
            "videos": result.media.get("videos", []),
            "screenshot": result.screenshot
        }
```

## Session Management

Handle sessions for sites requiring cookies:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def extract_with_session(url: str, cookies: dict = None):
    """Extract with custom browser session"""
    
    browser_config = BrowserConfig(
        headless=True,
        verbose=True,
        extra_args=["--disable-blink-features=AutomationControlled"]
    )
    
    run_config = CrawlerRunConfig(
        cookies=cookies,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; SanadBot/1.0; +https://sanad.ai)"
        }
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        return result.markdown
```

## Error Handling

Handle common crawling errors:

```python
async def extract_with_retry(url: str, max_retries: int = 3):
    """Extract with retry logic"""
    
    for attempt in range(max_retries):
        try:
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(url)
                
                # Validate extraction
                if result.success and len(result.markdown) > 100:
                    return {"success": True, "content": result.markdown}
                
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "success": False,
                    "error": str(e),
                    "url": url
                }
            
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Output Format

```python
{
    "url": str,
    "platform": "salla" | "zid" | "shopify" | "unknown",
    "markdown": str,  # Clean LLM-native content
    "html": str,      # Raw HTML
    "jsonld": [...],  # Structured data
    "media": {
        "images": [...],
        "videos": [...]
    },
    "success": bool
}
```

## Critical Rules

- Always use `AsyncWebCrawler` for performance
- Set `word_count_threshold` to filter navigation noise
- Extract JSON-LD separately from HTML content
- For bilingual sites, extract both `/ar` and `/en` versions
- Use `exclude_external_links=True` to focus on product content
- Handle Cloudflare/bot protection with appropriate headers
