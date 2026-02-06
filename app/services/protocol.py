"""AEO Protocol Checker Service

Validates AEO protocol compliance:
- llms.txt and llms-full.txt
- agent-card.json (Google A2A)
- robots.txt AI agent rules
"""

import httpx
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse


async def check_aeo_protocols(base_url: str) -> Dict:
    """
    Check all AEO protocol files for a given URL
    
    Args:
        base_url: The base URL to check (e.g., https://store.salla.sa)
    
    Returns:
        Dictionary with results for llms_txt, agent_card, and robots_txt
    """
    
    domain = extract_domain(base_url)
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # Run checks in parallel
        import asyncio
        llms_txt, agent_card, robots_txt = await asyncio.gather(
            check_llms_txt(client, domain),
            check_agent_card(client, domain),
            check_robots_txt(client, domain)
        )
    
    return {
        "llms_txt": llms_txt,
        "agent_card": agent_card,
        "robots_txt": robots_txt
    }


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


async def check_llms_txt(client: httpx.AsyncClient, domain: str) -> Dict:
    """
    Check /llms.txt file existence and structure
    
    Expected structure:
    - H1 title (starts with #)
    - Blockquote summary (contains >)
    - H2 sections with links
    """
    
    try:
        response = await client.get(f"{domain}/llms.txt")
        
        if response.status_code == 404:
            return {
                "status": "missing",
                "severity": "high",
                "issue": "llms.txt not found at domain root",
                "recommendation": "Create /llms.txt file following the standard format"
            }
        
        if response.status_code != 200:
            return {
                "status": "error",
                "severity": "medium",
                "issue": f"HTTP {response.status_code} when accessing llms.txt",
                "recommendation": "Ensure llms.txt is publicly accessible"
            }
        
        content = response.text
        
        # Validate structure
        has_h1 = content.strip().startswith("#") and "\n" in content
        has_blockquote = ">" in content
        has_h2 = "##" in content
        
        # Check for llms-full.txt reference
        has_full_reference = "llms-full.txt" in content.lower()
        
        if has_h1 and has_blockquote:
            return {
                "status": "found",
                "severity": "none",
                "valid_structure": True,
                "has_h1": has_h1,
                "has_blockquote": has_blockquote,
                "has_h2_sections": has_h2,
                "references_full": has_full_reference,
                "content_length": len(content)
            }
        else:
            return {
                "status": "found",
                "severity": "medium",
                "valid_structure": False,
                "issue": "llms.txt exists but doesn't follow standard format",
                "recommendation": "Add H1 title and blockquote summary",
                "has_h1": has_h1,
                "has_blockquote": has_blockquote
            }
        
    except httpx.TimeoutException:
        return {
            "status": "error",
            "severity": "medium",
            "issue": "Timeout when accessing llms.txt"
        }
    except Exception as e:
        return {
            "status": "error",
            "severity": "low",
            "issue": f"Error checking llms.txt: {str(e)}"
        }


async def check_agent_card(client: httpx.AsyncClient, domain: str) -> Dict:
    """
    Check /.well-known/agent-card.json (Google A2A Protocol)
    
    Expected: JSON-RPC 2.0 structure with schema, skills, endpoints
    """
    
    try:
        response = await client.get(f"{domain}/.well-known/agent-card.json")
        
        if response.status_code == 404:
            return {
                "status": "missing",
                "severity": "medium",
                "issue": "agent-card.json not found",
                "recommendation": "Create /.well-known/agent-card.json for Google A2A protocol support"
            }
        
        if response.status_code != 200:
            return {
                "status": "error",
                "severity": "medium",
                "issue": f"HTTP {response.status_code} when accessing agent-card.json"
            }
        
        # Parse JSON
        try:
            data = response.json()
        except Exception:
            return {
                "status": "invalid",
                "severity": "high",
                "issue": "agent-card.json is not valid JSON",
                "recommendation": "Fix JSON syntax errors"
            }
        
        # Validate A2A structure
        has_schema = "schema" in data or "$schema" in data
        has_skills = "skills" in data
        has_endpoints = "endpoints" in data
        
        if has_schema and (has_skills or has_endpoints):
            return {
                "status": "found",
                "severity": "none",
                "schema_valid": True,
                "has_schema": has_schema,
                "has_skills": has_skills,
                "has_endpoints": has_endpoints,
                "skills_count": len(data.get("skills", [])),
                "endpoints_count": len(data.get("endpoints", []))
            }
        else:
            return {
                "status": "found",
                "severity": "high",
                "schema_valid": False,
                "issue": "agent-card.json missing required fields",
                "recommendation": "Add 'schema', 'skills', and 'endpoints' fields",
                "has_schema": has_schema,
                "has_skills": has_skills,
                "has_endpoints": has_endpoints
            }
        
    except httpx.TimeoutException:
        return {
            "status": "error",
            "severity": "medium",
            "issue": "Timeout when accessing agent-card.json"
        }
    except Exception as e:
        return {
            "status": "error",
            "severity": "low",
            "issue": f"Error checking agent-card.json: {str(e)}"
        }


async def check_robots_txt(client: httpx.AsyncClient, domain: str) -> Dict:
    """
    Check /robots.txt for AI agent rules
    
    Checks for:
    - GPTBot, ClaudeBot, CCBot, PerplexityBot, Applebot-Extended, Bytespider
    - Sitemap directive
    """
    
    AI_USER_AGENTS = [
        "GPTBot",
        "ClaudeBot", 
        "CCBot",
        "PerplexityBot",
        "Applebot-Extended",
        "Bytespider"
    ]
    
    try:
        response = await client.get(f"{domain}/robots.txt")
        
        if response.status_code == 404:
            return {
                "status": "missing",
                "severity": "low",
                "issue": "robots.txt not found",
                "recommendation": "Create robots.txt with AI agent rules and Sitemap"
            }
        
        if response.status_code != 200:
            return {
                "status": "error",
                "severity": "low",
                "issue": f"HTTP {response.status_code} when accessing robots.txt"
            }
        
        content = response.text
        
        # Check for AI agents
        ai_agents_mentioned = []
        ai_agents_blocked = []
        
        for agent in AI_USER_AGENTS:
            if f"User-agent: {agent}" in content or f"User-agent: *" in content:
                ai_agents_mentioned.append(agent)
                
                # Check if explicitly disallowed
                # Simple heuristic: if "Disallow: /" appears after User-agent line
                if f"User-agent: {agent}" in content:
                    agent_section = content.split(f"User-agent: {agent}")[1].split("User-agent:")[0]
                    if "Disallow: /" in agent_section and "Allow:" not in agent_section:
                        ai_agents_blocked.append(agent)
        
        # Check for Sitemap
        has_sitemap = "Sitemap:" in content
        sitemap_urls = []
        if has_sitemap:
            for line in content.split("\n"):
                if line.startswith("Sitemap:"):
                    sitemap_urls.append(line.split("Sitemap:")[1].strip())
        
        severity = "none"
        issues = []
        
        if ai_agents_blocked:
            severity = "critical"
            issues.append(f"AI agents are blocked: {', '.join(ai_agents_blocked)}")
        
        if not has_sitemap:
            if severity == "none":
                severity = "low"
            issues.append("No Sitemap directive found")
        
        return {
            "status": "found",
            "severity": severity,
            "ai_agents_mentioned": ai_agents_mentioned,
            "ai_agents_blocked": ai_agents_blocked,
            "sitemap_present": has_sitemap,
            "sitemap_urls": sitemap_urls,
            "issues": issues if issues else None,
            "recommendation": "Allow AI agents and add Sitemap" if issues else None
        }
        
    except httpx.TimeoutException:
        return {
            "status": "error",
            "severity": "medium",
            "issue": "Timeout when accessing robots.txt"
        }
    except Exception as e:
        return {
            "status": "error",
            "severity": "low",
            "issue": f"Error checking robots.txt: {str(e)}"
        }
