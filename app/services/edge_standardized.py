"""
Standardized Edge Visibility Wrapper

Wraps edge_visibility.py to return standardized JSON with all 7 AI agents.
"""
from typing import Dict, List
import time


async def test_edge_visibility_standardized(url: str) -> Dict:
    """
    Test AI agent accessibility and return standardized format
    
    Returns:
        {
            "agents": [...],
            "cloudflare_detected": bool,
            "bot_challenge_enabled": bool,
            "score": 0-100
        }
    """
    import httpx
    
    # Define 7 AI agents to test
    ai_agents = [
        {"name": "ChatGPT", "icon": "🤖", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ChatGPT-User/1.0; +https://openai.com/bot)"},
        {"name": "Claude", "icon": "🔮", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +https://www.anthropic.com)"},
        {"name": "Perplexity", "icon": "🔍", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/bot)"},
        {"name": "Gemini", "icon": "✨", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +https://www.google.com/bot.html)"},
        {"name": "Copilot", "icon": "💼", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +https://www.bing.com/bingbot.htm)"},
        {"name": "You.com", "icon": "🌐", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; YouBot/1.0; +https://you.com/bot)"},
        {"name": "Jasper", "icon": "📝", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; JasperBot/1.0)"}
    ]
    
    agents_results = []
    cloudflare_detected = False
    bot_challenge_enabled = False
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for agent in ai_agents:
            try:
                start_time = time.time()
                
                response = await client.get(
                    url,
                    headers={"User-Agent": agent["user_agent"]}
                )
                
                response_time_ms = int((time.time() - start_time) * 1000)
                
                # Detect Cloudflare
                if "cf-ray" in response.headers or "cloudflare" in response.text.lower():
                    cloudflare_detected = True
                
                # Detect bot challenges
                if "challenge" in response.text.lower() or response.status_code == 403:
                    bot_challenge_enabled = True
                    status = "blocked"
                    data_completeness = "None"
                elif response.status_code == 200:
                    status = "accessible"
                    # Check data completeness based on content length
                    if len(response.text) > 5000:
                        data_completeness = "Full"
                    elif len(response.text) > 1000:
                        data_completeness = "Partial"
                    else:
                        data_completeness = "None"
                else:
                    status = "degraded"
                    data_completeness = "Partial"
                
            except Exception:
                status = "blocked"
                response_time_ms = 0
                data_completeness = "None"
            
            agents_results.append({
                "name": agent["name"],
                "icon": agent["icon"],
                "status": status,
                "response_time_ms": response_time_ms,
                "data_completeness": data_completeness
            })
    
    # Calculate score
    accessible_count = sum(1 for a in agents_results if a["status"] == "accessible")
    score = round((accessible_count / len(agents_results)) * 100)
    
    return {
        "agents": agents_results,
        "cloudflare_detected": cloudflare_detected,
        "bot_challenge_enabled": bot_challenge_enabled,
        "score": score
    }
