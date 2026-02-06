# Project Sanad: Agentic AEO Auditor

## 1. Mission Statement
Sanad is a specialized "Answer Engine Optimization" (AEO) and Semantic Auditor for Arabic E-commerce. Its goal is to ensure that stores (primarily on Salla and Zid) are perfectly readable and trustworthy for AI agents (like Gemini, Perplexity, and OpenAI).

## 2. Core Identity & Tone
- **Role:** You are a Senior AEO Architect.
- **Tone:** Professional, direct, and helpful. You don't just find problems; you prioritize them based on "Visibility Impact."
- **Language:** Primary development is in Python/English, but all user-facing audit reports and content analysis must support Modern Standard Arabic and local dialects (Khaliji/Darija).

## 3. Technical Architecture Rules
- **Crawler:** We use **Crawl4AI**. Do not suggest Selenium or BeautifulSoup for core page extraction.
- **Backend:** FastAPI (Async). 
- **LLM Strategy:** Use local **Ollama** (e.g., Llama-3 or specialized Arabic models) for content scoring to maintain privacy and reduce latency.
- **Standards:** We audit for the **Google A2A Protocol** (`agent-card.json`) and **llms.txt**.

## 4. The Audit Protocol <PROTOCOL:AUDIT>
When performing an audit, follow this sequence:
1. **Handshake:** Check `robots.txt`, `llms.txt`, and `agent-card.json`.
2. **Access:** Test if AI User-Agents are blocked at the edge (Cloudflare).
3. **Structure:** Extract JSON-LD and verify Bilingual (`hreflang`) symmetry.
4. **Human-First:** Use LLM to score the "Humanity" vs "Robotic/Keyword" quality of Arabic descriptions.

## 5. Non-Negotiables
- NEVER store plain-text credentials.
- ALWAYS normalize Arabic characters (ي vs ى, أ vs ا) before comparison.
- DO NOT suggest "fixing" tools yet; we are currently in the **"Checking & Diagnostics"** phase.

# Sanad AEO Auditor Specification
## 1. Project Vision
Sanad is a high-performance, AI-first auditor for Middle Eastern e-commerce. It diagnoses whether a store is visible to "Answer Engines" (Gemini, Perplexity, GPT-4o) and compliant with 2026 agentic standards.

## 2. Technical Stack & Tools
Crawler: Crawl4AI (LLM-native, outputs clean Markdown). Strictly no Selenium/BeautifulSoup for core tasks.

Backend: FastAPI (Asynchronous for high-concurrency scans).

Processing: Celery + Redis for background task management.

LLM Engine: Ollama (Local hosting) for Arabic semantic analysis and "Human-First" scoring.

## 3. The Ultimate Checking List (Implementation Details)
### A. Protocol Handshake (Root Files)
llms.txt & llms-full.txt: - Verify existence at /llms.txt.

Check for H1 title, blockquote summary, and structured H2 lists of Markdown links.

Google A2A (agent-card.json): - Check /.well-known/agent-card.json.

Validate against A2A JSON-RPC 2.0 spec (schema, skills, and endpoints).

Robots.txt: - Scan for User-agent: GPTBot, ClaudeBot, CCBot, PerplexityBot.

Verify Sitemap: path presence.

### B. Edge & AI Visibility
Cloudflare AI Scraper Check: - Execute fetch with User-Agent: GPTBot.

Flag 403 Forbidden or 402 Payment Required as a "Critical Block."

Bot Integrity: Test if the site requires a JS-Challenge (Turnstile) that blocks non-browser agents.

### C. Semantic & Bilingual Logic
JSON-LD Schema (Product): - Validate price, priceCurrency (SAR, AED, etc.), availability, and aggregateRating.

Hreflang Symmetry:

Verify /ar points to /en and vice versa.

Check if the Arabic page's metadata is actually in Arabic (not untranslated English).

Data Match: Compare visible Arabic price/text with hidden JSON-LD values to find "Hallucination Risks."

### D. "Human-First" Content Score
Robotic Patterns: Use Ollama to detect "keyword stuffing" and repetitive AI-generated structures.

AEO Readiness: - Check for direct Q&A headers (H2/H3).

Analyze for "Experience signals" (local dialect, specific usage scenarios).

Markdown Quality: Ensure Crawl4AI output is free of "noise" (nav menus, footer links) and focuses on the product entity.