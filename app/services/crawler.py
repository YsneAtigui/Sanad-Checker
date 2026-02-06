"""Crawl4AI Content Extractor Service

Extract clean, LLM-native content from Arabic e-commerce sites using Crawl4AI.
"""

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import json
import asyncio


async def extract_page_content(url: str) -> Dict:
    """
    Extract clean content from a product page
    
    Args:
        url: Product page URL
    
    Returns:
        Dictionary with markdown, html, jsonld, platform, and media
    """
    
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
    )
    
    crawler_config = CrawlerRunConfig(
        word_count_threshold=10,  # Filter short noise
        exclude_external_links=True,
        exclude_social_media_links=True,
        remove_overlay_elements=True,
        screenshot=True,  # Capture screenshot for audit
    )
    
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=crawler_config)
            
            if not result.success:
                return {
                    "success": False,
                    "error": "Crawl failed",
                    "url": url
                }
            
            # Detect platform
            platform = detect_platform(url, result.html)
            
            # Extract JSON-LD
            jsonld_data = extract_jsonld_from_html(result.html)
            
            # Extract media (filter out icons/logos)
            media = extract_media_from_result(result)
            
            # Handle markdown (fit_markdown is now markdown.fit_markdown in newer versions)
            markdown_fit = None
            if hasattr(result, 'markdown') and hasattr(result.markdown, 'fit_markdown'):
                markdown_fit = result.markdown.fit_markdown
            elif hasattr(result.markdown, 'fit_markdown'):
                markdown_fit = result.markdown.fit_markdown
            
            return {
                "success": True,
                "url": url,
                "platform": platform,
                "markdown": str(result.markdown) if result.markdown else "",
                "markdown_fit": markdown_fit,  # Filtered for relevance (if available)
                "html": result.html,
                "jsonld": jsonld_data,
                "media": media,
                "screenshot": result.screenshot,
                "links": result.links
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }


def detect_platform(url: str, html: str) -> str:
    """Detect e-commerce platform"""
    
    if "salla.sa" in url or "cdn.salla.network" in html or "salla-cdn" in html:
        return "salla"
    elif "zid.sa" in url or "cdn.zid" in html:
        return "zid"
    elif "shopify" in html or "cdn.shopify.com" in html:
        return "shopify"
    else:
        return "unknown"


def extract_jsonld_from_html(html: str) -> List[Dict]:
    """Extract JSON-LD structured data from HTML"""
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script', type='application/ld+json')
        
        jsonld_data = []
        for script in scripts:
            try:
                if script.string:
                    data = json.loads(script.string)
                    jsonld_data.append(data)
            except json.JSONDecodeError:
                continue
        
        return jsonld_data
    except Exception:
        return []


def extract_media_from_result(result) -> Dict:
    """Extract and filter media (images, videos)"""
    
    # Filter out logos, icons, favicons
    excluded_keywords = ["logo", "icon", "favicon", "sprite", "placeholder"]
    
    product_images = []
    if hasattr(result, 'media') and result.media:
        images = result.media.get("images", [])
        for img in images:
            src = img.get("src", "").lower()
            # Skip if it's a logo/icon or too small
            if not any(keyword in src for keyword in excluded_keywords):
                product_images.append(img)
    
    return {
        "images": product_images,
        "videos": result.media.get("videos", []) if hasattr(result, 'media') and result.media else []
    }


async def extract_bilingual_content(url: str) -> Dict:
    """
    Extract both Arabic and English versions of a page
    
    Args:
        url: Base URL (can have /ar or /en or neither)
    
    Returns:
        Dictionary with both language versions
    """
    
    from urllib.parse import urlparse, urlunparse
    
    parsed = urlparse(url)
    path = parsed.path
    
    # Remove trailing slash
    path = path.rstrip('/')
    
    # Detect if URL already has language code
    has_ar = path.startswith('/ar/') or path == '/ar'
    has_en = path.startswith('/en/') or path == '/en'
    
    if has_ar:
        # Remove /ar prefix to get base path
        base_path = path[3:] if path.startswith('/ar/') else '/'
        ar_path = path
        en_path = '/en' + base_path
    elif has_en:
        # Remove /en prefix to get base path
        base_path = path[3:] if path.startswith('/en/') else '/'
        ar_path = '/ar' + base_path
        en_path = path
    else:
        # No language prefix, add both
        ar_path = '/ar' + path
        en_path = '/en' + path
    
    # Construct full URLs
    ar_url = urlunparse((parsed.scheme, parsed.netloc, ar_path, '', '', ''))
    en_url = urlunparse((parsed.scheme, parsed.netloc, en_path, '', '', ''))
    
    # Extract both concurrently
    ar_result, en_result = await asyncio.gather(
        extract_page_content(ar_url),
        extract_page_content(en_url),
        return_exceptions=True
    )
    
    return {
        "arabic": ar_result if not isinstance(ar_result, Exception) else {"success": False, "error": str(ar_result)},
        "english": en_result if not isinstance(en_result, Exception) else {"success": False, "error": str(en_result)}
    }


async def extract_with_retry(url: str, max_retries: int = 3) -> Dict:
    """
    Extract content with retry logic and exponential backoff
    
    Args:
        url: URL to extract
        max_retries: Maximum retry attempts
    
    Returns:
        Extraction result
    """
    
    for attempt in range(max_retries):
        try:
            result = await extract_page_content(url)
            
            # Validate extraction quality
            if result.get("success") and len(result.get("markdown", "")) > 100:
                return result
            
            # If last attempt, return whatever we got
            if attempt == max_retries - 1:
                return result
                
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "success": False,
                    "error": f"Failed after {max_retries} attempts: {str(e)}",
                    "url": url
                }
            
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)
    
    return {"success": False, "error": "Extraction failed", "url": url}
