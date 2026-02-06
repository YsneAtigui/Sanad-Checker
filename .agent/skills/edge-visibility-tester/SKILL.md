---
name: edge-visibility-tester
description: Test if AI agents are blocked at the network edge (Cloudflare, CDN). Detect bot challenges, 403 errors, and JS-based blocking. Use when diagnosing why AI agents cannot access a site or validating edge configuration for Answer Engine compliance.
---

# Edge Visibility Tester

Test network edge visibility for AI User-Agents to diagnose blocking issues.

## AI User-Agent Testing

Test multiple AI agent User-Agents:

```python
import httpx

AI_USER_AGENTS = {
    "gptbot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.0; +https://openai.com/gptbot)",
    "claudebot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +https://www.anthropic.com)",
    "perplexitybot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/bot)",
    "ccbot": "CCBot/2.0 (+https://commoncrawl.org/faq/)",
    "applebot": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko; compatible; Applebot-Extended/1.0; +https://support.apple.com/)",
    "bingbot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
}

async def test_ai_agent_access(url: str):
    """Test access for all major AI agents"""
    
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
                    "severity": "critical"
                }
    
    return results
```

## Response Analysis

Detect different types of blocking:

```python
def analyze_response(response: httpx.Response, agent_name: str) -> dict:
    """Analyze HTTP response for blocking signals"""
    
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
            "blocked_by": "cloudflare"
        }
    
    # Turnstile challenge
    if "turnstile" in content or "cf-turnstile" in content:
        return {
            "accessible": False,
            "reason": "Cloudflare Turnstile (JS challenge)",
            "severity": "critical",
            "blocked_by": "cloudflare_turnstile"
        }
    
    # reCAPTCHA detection
    if "recaptcha" in content or "g-recaptcha" in content:
        return {
            "accessible": False,
            "reason": "reCAPTCHA challenge",
            "severity": "high",
            "blocked_by": "recaptcha"
        }
    
    # Akamai/Bot Manager
    if "akamai" in headers.get("server", "").lower():
        if status_code in [403, 429]:
            return {
                "accessible": False,
                "reason": "Akamai Bot Manager",
                "severity": "critical",
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
            "reason": "Empty or minimal content despite 200 OK",
            "severity": "medium",
            "content_length": len(content)
        }
    
    return {
        "accessible": "unknown",
        "status_code": status_code,
        "severity": "medium"
    }
```

## Cloudflare Specific Detection

Detailed Cloudflare configuration check:

```python
async def check_cloudflare_config(domain: str):
    """Check Cloudflare AI scraper settings"""
    
    # Test with CF-specific headers
    async with httpx.AsyncClient() as client:
        
        # Test 1: Standard bot
        bot_response = await client.get(
            f"https://{domain}",
            headers={"User-Agent": "GPTBot/1.0"}
        )
        
        # Test 2: Browser-like with bot header
        hybrid_response = await client.get(
            f"https://{domain}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate"
            }
        )
        
        # Analyze differences
        bot_blocked = bot_response.status_code in [403, 503]
        browser_ok = hybrid_response.status_code == 200
        
        if bot_blocked and browser_ok:
            return {
                "cloudflare_configured": True,
                "blocks_ai_agents": True,
                "reason": "User-Agent based blocking (likely CF AI Scraper Protection enabled)",
                "recommendation": "Disable 'Bot Fight Mode' or add AI bots to allowlist"
            }
        
        # Check for Cloudflare headers
        cf_headers = {
            "cf-ray": bot_response.headers.get("cf-ray"),
            "cf-cache-status": bot_response.headers.get("cf-cache-status"),
            "server": bot_response.headers.get("server")
        }
        
        return {
            "cloudflare_configured": "cloudflare" in str(cf_headers).lower(),
            "blocks_ai_agents": bot_blocked,
            "cf_headers": cf_headers
        }
```

## Rate Limiting Detection

Test for aggressive rate limiting:

```python
async def test_rate_limits(url: str, requests: int = 5):
    """Test if site rate-limits bot requests"""
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for i in range(requests):
            response = await client.get(
                url,
                headers={"User-Agent": "GPTBot/1.0"}
            )
            
            results.append({
                "request_num": i + 1,
                "status_code": response.status_code,
                "timestamp": time.time()
            })
            
            # Small delay
            await asyncio.sleep(0.5)
    
    # Analyze pattern
    status_codes = [r["status_code"] for r in results]
    
    if 429 in status_codes:
        return {
            "rate_limited": True,
            "after_requests": status_codes.index(429) + 1,
            "severity": "high"
        }
    
    # Progressive degradation
    if len(set(status_codes)) > 1 and 403 in status_codes:
        return {
            "rate_limited": True,
            "pattern": "progressive_blocking",
            "severity": "high"
        }
    
    return {
        "rate_limited": False,
        "all_accessible": all(c == 200 for c in status_codes)
    }
```

## JS Challenge Detection

Check for JavaScript-based challenges:

```python
def detect_js_challenge(html_content: str) -> dict:
    """Detect if page requires JavaScript execution"""
    
    # Meta refresh redirects (often used in JS challenges)
    if 'http-equiv="refresh"' in html_content.lower():
        return {
            "js_challenge": True,
            "type": "meta_refresh",
            "severity": "critical"
        }
    
    # Minimal HTML with script tags
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    text_content = soup.get_text(strip=True)
    script_tags = soup.find_all('script')
    
    # Suspiciously small content with many scripts
    if len(text_content) < 200 and len(script_tags) > 3:
        return {
            "js_challenge": True,
            "type": "script_heavy_minimal_content",
            "severity": "high",
            "script_count": len(script_tags)
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
            "severity": "medium"
        }
    
    return {
        "js_challenge": False
    }
```

## Comprehensive Edge Test

Complete edge visibility check:

```python
async def comprehensive_edge_test(url: str):
    """Full edge visibility audit"""
    
    results = {
        "url": url,
        "tested_at": datetime.now().isoformat()
    }
    
    # Test all AI agents
    ai_agent_results = await test_ai_agent_access(url)
    results["ai_agents"] = ai_agent_results
    
    # Cloudflare check
    domain = url.split("//")[1].split("/")[0]
    cf_check = await check_cloudflare_config(domain)
    results["cloudflare"] = cf_check
    
    # Rate limit test
    rate_test = await test_rate_limits(url)
    results["rate_limiting"] = rate_test
    
    # Summary
    blocked_count = sum(
        1 for agent, data in ai_agent_results.items()
        if not data.get("accessible")
    )
    
    results["summary"] = {
        "total_agents_tested": len(AI_USER_AGENTS),
        "blocked_agents": blocked_count,
        "accessible": blocked_count == 0,
        "severity": "critical" if blocked_count > 0 else "none"
    }
    
    return results
```

## Output Format

```python
{
    "ai_agents": {
        "gptbot": {
            "accessible": False,
            "reason": "Cloudflare bot challenge",
            "severity": "critical"
        },
        "claudebot": {...},
        ...
    },
    "cloudflare": {
        "blocks_ai_agents": True,
        "recommendation": "..."
    },
    "rate_limiting": {
        "rate_limited": False
    },
    "summary": {
        "blocked_agents": 3,
        "accessible": False,
        "severity": "critical"
    }
}
```

## Critical Rules

- Test multiple AI User-Agents (GPTBot, ClaudeBot, etc.)
- Cloudflare Bot Fight Mode is the most common blocker
- Status 403/402 for bots but 200 for browsers = User-Agent blocking
- JS challenges (Turnstile) block AI agents by default
- Always compare bot vs browser-like requests
- Empty 200 responses are suspicious (possible cloaking)
