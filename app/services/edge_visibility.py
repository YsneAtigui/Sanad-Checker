"""Edge Visibility Tester Service

Test if AI agents are blocked at the network edge (Cloudflare, CDN, etc.).
"""

import httpx
import asyncio
from typing import Dict, List
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse


# AI User-Agents to test
AI_USER_AGENTS = {
    "gptbot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.0; +https://openai.com/gptbot)",
    "claudebot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +https://www.anthropic.com)",
    "perplexitybot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/bot)",
    "ccbot": "CCBot/2.0 (+https://commoncrawl.org/faq/)",
    "applebot": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko; compatible; Applebot-Extended/1.0; +https://support.apple.com/)",
    "bingbot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
}


async def test_ai_agent_access(url: str) -> Dict:
    """
    Test access for all major AI agents
    
    Args:
        url: URL to test
    
    Returns:
        Dictionary with results for each AI agent
    """
    
    results = {}
    
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True
    ) as client:
        
        for agent_name, user_agent in AI_USER_AGENTS.items():
            try:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                    }
                )
                
                results[agent_name] = analyze_response(response, agent_name)
                
            except Exception as e:
                results[agent_name] = {
                    "accessible": False,
                    "error": str(e),
                    "severity": "critical",
                    "reason": f"Request failed: {str(e)}"
                }
    
    return results


def analyze_response(response: httpx.Response, agent_name: str) -> Dict:
    """
    Analyze HTTP response for blocking signals
    
    Args:
        response: HTTP response object
        agent_name: Name of the AI agent
    
    Returns:
        Analysis results
    """
    
    status_code = response.status_code
    content = response.text.lower()
    headers = response.headers
    
    # HTTP-level blocking
    if status_code == 403:
        return {
            "accessible": False,
            "reason": "HTTP 403 Forbidden",
            "severity": "critical",
            "status_code": 403
        }
    
    if status_code == 402:
        return {
            "accessible": False,
            "reason": "HTTP 402 Payment Required (Rate limited)",
            "severity": "critical",
            "status_code": 402
        }
    
    if status_code == 429:
        return {
            "accessible": False,
            "reason": "HTTP 429 Too Many Requests (Rate limited)",
            "severity": "critical",
            "status_code": 429
        }
    
    # Cloudflare challenge detection
    cf_challenge = any([
        "cf-chl" in content,
        "just a moment" in content,
        "checking your browser" in content,
        "cloudflare" in content and "challenge" in content,
        "ray id" in content and status_code in [403, 503]
    ])
    
    if cf_challenge:
        return {
            "accessible": False,
            "reason": "Cloudflare bot challenge",
            "severity": "critical",
            "status_code": status_code,
            "blocked_by": "cloudflare"
        }
    
    # Turnstile challenge
    if "turnstile" in content or "cf-turnstile" in content:
        return {
            "accessible": False,
            "reason": "Cloudflare Turnstile (JS challenge)",
            "severity": "critical",
            "status_code": status_code,
            "blocked_by": "cloudflare_turnstile"
        }
    
    # reCAPTCHA detection
    if "recaptcha" in content or "g-recaptcha" in content:
        return {
            "accessible": False,
            "reason": "reCAPTCHA challenge",
            "severity": "high",
            "status_code": status_code,
            "blocked_by": "recaptcha"
        }
    
    # Akamai/Bot Manager
    if "akamai" in headers.get("server", "").lower():
        if status_code in [403, 429]:
            return {
                "accessible": False,
                "reason": "Akamai Bot Manager",
                "severity": "critical",
                "status_code": status_code,
                "blocked_by": "akamai"
            }
    
    # Generic bot detection page
    if any(phrase in content for phrase in [
        "access denied", "bot detected", "automated access",
        "suspicious activity", "unusual traffic"
    ]):
        return {
            "accessible": False,
            "reason": "Generic bot detection",
            "severity": "high",
            "status_code": status_code,
            "blocked_by": "unknown"
        }
    
    # Success - accessible
    if status_code == 200 and len(content) > 1000:
        return {
            "accessible": True,
            "status_code": 200,
            "content_length": len(content),
            "severity": "none"
        }
    
    # Suspicious - empty response
    if status_code == 200 and len(content) < 100:
        return {
            "accessible": "suspicious",
            "reason": "Empty or minimal content despite 200 OK (possible cloaking)",
            "severity": "medium",
            "status_code": 200,
            "content_length": len(content)
        }
    
    return {
        "accessible": "unknown",
        "status_code": status_code,
        "content_length": len(content),
        "severity": "medium"
    }


async def check_cloudflare_config(domain: str) -> Dict:
    """
    Check Cloudflare AI scraper settings
    
    Args:
        domain: Domain to check (without protocol)
    
    Returns:
        Cloudflare configuration analysis
    """
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # Test 1: Standard bot
            bot_response = await client.get(
                f"https://{domain}",
                headers={"User-Agent": "GPTBot/1.0"},
                follow_redirects=True
            )
            
            # Test 2: Browser-like
            browser_response = await client.get(
                f"https://{domain}",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate"
                },
                follow_redirects=True
            )
            
            # Analyze differences
            bot_blocked = bot_response.status_code in [403, 503, 429]
            browser_ok = browser_response.status_code == 200
            
            # Check for Cloudflare headers
            cf_headers = {
                "cf-ray": bot_response.headers.get("cf-ray"),
                "cf-cache-status": bot_response.headers.get("cf-cache-status"),
                "server": bot_response.headers.get("server")
            }
            
            is_cloudflare = "cloudflare" in str(cf_headers).lower() or cf_headers.get("cf-ray") is not None
            
            if bot_blocked and browser_ok:
                return {
                    "cloudflare_detected": is_cloudflare,
                    "blocks_ai_agents": True,
                    "severity": "critical",
                    "reason": "User-Agent based blocking detected",
                    "recommendation": "Disable 'Bot Fight Mode' or add AI bots to allowlist in Cloudflare settings",
                    "bot_status": bot_response.status_code,
                    "browser_status": browser_response.status_code,
                    "cf_headers": cf_headers
                }
            
            return {
                "cloudflare_detected": is_cloudflare,
                "blocks_ai_agents": bot_blocked,
                "severity": "critical" if bot_blocked else "none",
                "bot_status": bot_response.status_code,
                "browser_status": browser_response.status_code,
                "cf_headers": cf_headers
            }
            
    except Exception as e:
        return {
            "cloudflare_detected": False,
            "error": str(e),
            "severity": "medium"
        }


def detect_js_challenge(html_content: str) -> Dict:
    """
    Detect if page requires JavaScript execution
    
    Args:
        html_content: HTML content to analyze
    
    Returns:
        JS challenge detection results
    """
    
    # Meta refresh redirects (often used in JS challenges)
    if 'http-equiv="refresh"' in html_content.lower():
        return {
            "js_challenge": True,
            "type": "meta_refresh",
            "severity": "critical"
        }
    
    # Minimal HTML with script tags
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        text_content = soup.get_text(strip=True)
        script_tags = soup.find_all('script')
        
        # Suspiciously small content with many scripts
        if len(text_content) < 200 and len(script_tags) > 3:
            return {
                "js_challenge": True,
                "type": "script_heavy_minimal_content",
                "severity": "high",
                "script_count": len(script_tags),
                "text_length": len(text_content)
            }
        
        # Common JS challenge patterns
        js_patterns = [
            "document.cookie",
            "window.location.href",
            "setTimeout",
            "challenge-platform"
        ]
        
        script_content = " ".join([s.get_text() for s in script_tags])
        pattern_matches = sum(1 for p in js_patterns if p in script_content)
        
        if pattern_matches >= 3:
            return {
                "js_challenge": "possible",
                "type": "redirect_scripts",
                "severity": "medium",
                "pattern_matches": pattern_matches
            }
        
        return {
            "js_challenge": False
        }
    except Exception:
        return {
            "js_challenge": False,
            "error": "Failed to parse HTML"
        }


async def comprehensive_edge_test(url: str) -> Dict:
    """
    Full edge visibility audit
    
    Args:
        url: URL to test
    
    Returns:
        Complete edge visibility test results
    """
    
    results = {
        "url": url,
        "tested_at": datetime.now().isoformat()
    }
    
    # Test all AI agents
    ai_agent_results = await test_ai_agent_access(url)
    results["ai_agents"] = ai_agent_results
    
    # Extract domain
    parsed = urlparse(url)
    domain = parsed.netloc
    
    # Cloudflare check
    cf_check = await check_cloudflare_config(domain)
    results["cloudflare"] = cf_check
    
    # Summary
    blocked_count = sum(
        1 for agent, data in ai_agent_results.items()
        if data.get("accessible") is False
    )
    
    suspicious_count = sum(
        1 for agent, data in ai_agent_results.items()
        if data.get("accessible") == "suspicious"
    )
    
    accessible_count = sum(
        1 for agent, data in ai_agent_results.items()
        if data.get("accessible") is True
    )
    
    # Determine overall severity
    if blocked_count > 0:
        severity = "critical"
    elif suspicious_count > 0:
        severity = "medium"
    else:
        severity = "none"
    
    results["summary"] = {
        "total_agents_tested": len(AI_USER_AGENTS),
        "accessible_agents": accessible_count,
        "blocked_agents": blocked_count,
        "suspicious_agents": suspicious_count,
        "fully_accessible": blocked_count == 0 and suspicious_count == 0,
        "severity": severity
    }
    
    return results
