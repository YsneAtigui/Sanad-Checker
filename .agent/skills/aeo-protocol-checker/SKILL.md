---
name: aeo-protocol-checker
description: Validate AEO (Answer Engine Optimization) protocol compliance for e-commerce sites. Check llms.txt, agent-card.json (Google A2A), and robots.txt configurations. Use when auditing AI agent visibility, checking protocol handshakes, or diagnosing why AI agents cannot access a site.
---

# AEO Protocol Checker

This skill validates that a website complies with AEO standards required for AI agent visibility.

## Protocol Files to Check

### 1. llms.txt & llms-full.txt

**Location:** `/llms.txt` and `/llms-full.txt` at domain root

**Validation steps:**
1. Fetch the file and check HTTP status (200 = exists, 404 = missing)
2. Verify structure:
   - H1 title at the top
   - Blockquote summary
   - H2 sections with Markdown links
3. Check for `llms-full.txt` reference if using abbreviated version

**Example validation:**
```python
import httpx

async def check_llms_txt(base_url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/llms.txt")
        if response.status_code == 404:
            return {"status": "missing", "severity": "high"}
        
        content = response.text
        has_h1 = content.startswith("#") and "\n" in content
        has_blockquote = ">" in content
        
        return {
            "status": "found",
            "has_structure": has_h1 and has_blockquote,
            "content": content
        }
```

### 2. Google A2A Protocol (agent-card.json)

**Location:** `/.well-known/agent-card.json`

**Validation steps:**
1. Fetch and parse JSON
2. Validate JSON-RPC 2.0 structure
3. Check required fields: `schema`, `skills`, `endpoints`
4. Verify endpoint URLs are accessible

**Reference:** See `references/a2a-schema.md` for complete JSON schema specification

### 3. robots.txt AI Agent Rules

**Location:** `/robots.txt`

**Check for AI User-Agents:**
- `User-agent: GPTBot`
- `User-agent: ClaudeBot` 
- `User-agent: CCBot`
- `User-agent: PerplexityBot`
- `User-agent: Applebot-Extended`
- `User-agent: Bytespider`

**Validation:**
```python
def check_ai_agent_access(robots_content: str):
    blocked_agents = []
    
    for ua in ["GPTBot", "ClaudeBot", "CCBot", "PerplexityBot"]:
        # Check if agent is explicitly disallowed
        if f"User-agent: {ua}" in robots_content:
            # Find disallow rules for this agent
            pass
    
    return blocked_agents
```

Also verify `Sitemap:` directive is present.

## Edge & Access Testing

Test if AI agents are blocked at edge (Cloudflare):

```python
async def test_ai_agent_access(url: str):
    headers = {"User-Agent": "GPTBot/1.0"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code in [403, 402]:
            return {"blocked": True, "severity": "critical"}
        
        # Check for Cloudflare challenge
        if "cf-chl" in response.text or "Just a moment" in response.text:
            return {"blocked": True, "reason": "cloudflare_challenge"}
        
        return {"blocked": False}
```

## Output Format

Return structured audit results:

```python
{
    "llms_txt": {
        "status": "found" | "missing" | "malformed",
        "severity": "low" | "medium" | "high"
    },
    "agent_card": {
        "status": "found" | "missing" | "invalid",
        "schema_valid": bool
    },
    "robots_txt": {
        "ai_agents_blocked": ["GPTBot", ...],
        "sitemap_present": bool
    },
    "edge_access": {
        "blocked": bool,
        "reason": str
    }
}
```

## Critical Rules

- Always use async HTTP clients (httpx) for concurrent checks
- Flag 403/402 responses to AI User-Agents as **CRITICAL**
- For Arabic e-commerce, check both `/ar/` and `/en/` paths if site is bilingual
- Normalize URLs (remove trailing slashes) before testing
