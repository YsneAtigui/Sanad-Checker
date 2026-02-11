"""Edge visibility service with standardized responses.

Tests AI agent accessibility and returns typed responses.
"""

from typing import List
import time

import httpx

from app.services.base_service import BaseService
from app.infrastructure.logging import log_performance
from app.application.dto import EdgeResponse, AgentAccessResult
from app.domain.exceptions import ServiceUnavailableError


class EdgeService(BaseService):
    """Service for AI agent accessibility testing.
    
    Tests whether AI agents can access the site at the network edge,
    detecting Cloudflare, bot challenges, and access restrictions.
    
    Example:
        ```python
        service = EdgeService()
        result = await service.test_visibility("https://example.com")
        print(f"Accessibility: {result.score}/100")
        for agent in result.agents:
            print(f"{agent.name}: {agent.status}")
        ```
    """
    
    # AI agents to test
    AI_AGENTS = [
        {"name": "ChatGPT", "icon": "🤖", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ChatGPT-User/1.0; +https://openai.com/bot)"},
        {"name": "Claude", "icon": "🔮", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +https://www.anthropic.com)"},
        {"name": "Perplexity", "icon": "🔍", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/bot)"},
        {"name": "Gemini", "icon": "✨", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +https://www.google.com/bot.html)"},
        {"name": "Copilot", "icon": "💼", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +https://www.bing.com/bingbot.htm)"},
        {"name": "You.com", "icon": "🌐", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; YouBot/1.0; +https://you.com/bot)"},
        {"name": "Jasper", "icon": "📝", "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; JasperBot/1.0)"}
    ]
    
    @log_performance
    async def test_visibility(self, url: str) -> EdgeResponse:
        """Test AI agent accessibility at network edge.
        
        Tests access for 7 major AI agents, detecting:
        - Cloudflare protection
        - Bot challenges
        - Access restrictions
        - Response times
        
        Args:
            url: URL to test
            
        Returns:
            EdgeResponse with agent results and detection flags
            
        Raises:
            ServiceUnavailableError: If service fails completely
            
        Example:
            >>> service = EdgeService()
            >>> response = await service.test_visibility("https://shop.example.com")
            >>> response.score
            86
            >>> response.cloudflare_detected
            True
        """
        self.logger.info("Testing edge visibility", extra={"url": url, "agents_count": len(self.AI_AGENTS)})
        
        agents_results = []
        cloudflare_detected = False
        bot_challenge_enabled = False
        
        timeout = httpx.Timeout(self.http_timeout, connect=5.0)
        
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                for agent in self.AI_AGENTS:
                    result = await self._test_agent(
                        client,
                        url,
                        agent,
                        cloudflare_detected,
                        bot_challenge_enabled
                    )
                    agents_results.append(result["agent_result"])
                    cloudflare_detected = cloudflare_detected or result["cf_detected"]
                    bot_challenge_enabled = bot_challenge_enabled or result["bot_challenge"]
            
            # Calculate score
            accessible_count = sum(
                1 for a in agents_results
                if a.status == "accessible"
            )
            score = round((accessible_count / len(agents_results)) * 100) if agents_results else 0
            
            response = EdgeResponse(
                agents=agents_results,
                cloudflare_detected=cloudflare_detected,
                bot_challenge_enabled=bot_challenge_enabled,
                score=score
            )
            
            self.logger.info(
                "Edge visibility test completed",
                extra={
                    "url": url,
                    "score": score,
                    "accessible_count": accessible_count,
                    "cloudflare": cloudflare_detected,
                    "bot_challenge": bot_challenge_enabled
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Edge visibility test failed: {str(e)}", exc_info=True)
            raise ServiceUnavailableError(
                service="Edge Visibility Test",
                reason=str(e),
                url=url
            )
    
    async def _test_agent(
        self,
        client: httpx.AsyncClient,
        url: str,
        agent: dict,
        cf_detected: bool,
        bot_challenge: bool
    ) -> dict:
        """Test accessibility for single AI agent.
        
        Args:
            client: HTTP client
            url: URL to test
            agent: Agent configuration dict
            cf_detected: Current Cloudflare detection status
            bot_challenge: Current bot challenge status
            
        Returns:
            Dict with agent_result, cf_detected, bot_challenge
        """
        try:
            start_time = time.time()
            
            response = await client.get(
                url,
                headers={"User-Agent": agent["user_agent"]}
            )
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Detect Cloudflare
            local_cf_detected = (
                "cf-ray" in response.headers or
                "cloudflare" in response.text.lower()
            )
            
            # Detect bot challenges
            local_bot_challenge = (
                "challenge" in response.text.lower() or
                response.status_code == 403
            )
            
            # Determine status and completeness
            if local_bot_challenge or response.status_code == 403:
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
            
        except Exception as e:
            self.logger.debug(f"Agent {agent['name']} test failed: {str(e)}")
            status = "blocked"
            response_time_ms = 0
            data_completeness = "None"
            local_cf_detected = False
            local_bot_challenge = False
        
        agent_result = AgentAccessResult(
            name=agent["name"],
            icon=agent["icon"],
            status=status,
            response_time_ms=response_time_ms,
            data_completeness=data_completeness
        )
        
        return {
            "agent_result": agent_result,
            "cf_detected": local_cf_detected,
            "bot_challenge": local_bot_challenge
        }


# Standalone wrapper function for backward compatibility
async def test_edge_visibility_standardized(url: str) -> dict:
    """Standalone wrapper for EdgeService.test_visibility.
    
    Args:
        url: URL to test
        
    Returns:
        Dictionary with edge visibility results (EdgeResponse as dict)
    """
    service = EdgeService()
    response = await service.test_visibility(url)
    
    # Convert to dict for backward compatibility
    return {
        "agents": [
            {
                "name": agent.name,
                "icon": agent.icon,
                "status": agent.status,
                "response_time_ms": agent.response_time_ms,
                "data_completeness": agent.data_completeness
            }
            for agent in response.agents
        ],
        "cloudflare_detected": response.cloudflare_detected,
        "bot_challenge_enabled": response.bot_challenge_enabled,
        "score": response.score
    }
