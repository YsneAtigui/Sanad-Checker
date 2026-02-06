---
name: human-first-scorer
description: Analyze Arabic content quality using Ollama LLM to detect robotic vs human-first writing. Score content for keyword stuffing, unnatural patterns, and AEO readiness. Use when auditing product descriptions, checking for AI-generated spam, or evaluating content authenticity.
---

# Human-First Content Scorer

Use local Ollama models to score Arabic e-commerce content for "humanity" vs robotic/SEO-stuffed patterns.

## Scoring Dimensions

Evaluate content across these dimensions:

1. **Naturalness** (0-10): How human/conversational the text feels
2. **Keyword Stuffing** (0-10): Repetition and unnatural keyword usage (lower is worse)
3. **AEO Readiness** (0-10): Structured for Q&A and direct answers
4. **Dialect Usage** (0-10): Presence of regional Arabic variants (authenticity signal)

## Ollama Integration

Use local Llama-3 or specialized Arabic models:

```python
import httpx

async def score_content_with_ollama(text: str, lang: str = "ar"):
    """
    Score content using local Ollama instance
    """
    
    prompt = f"""
You are an Arabic content quality analyzer for e-commerce.

Analyze this product description and score it (0-10) across these dimensions:
1. Naturalness: Does it sound human and conversational?
2. Keyword Stuffing: Is it repetitive or over-optimized? (10 = no stuffing, 0 = heavy stuffing)
3. AEO Readiness: Does it answer questions directly?
4. Dialect Usage: Does it use regional Arabic (Khaliji) naturally?

Text:
{text}

Return ONLY a JSON object:
{{
  "naturalness": <score>,
  "keyword_stuffing_reverse": <score>,
  "aeo_readiness": <score>,
  "dialect_usage": <score>,
  "reasoning": "<brief explanation>"
}}
"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",  # or "aya" for better Arabic support
                "prompt": prompt,
                "stream": False
            },
            timeout=30.0
        )
        
        result = response.json()
        return parse_ollama_response(result["response"])
```

## Robotic Pattern Detection

Pre-LLM heuristics to catch obvious issues:

```python
def detect_robotic_patterns(text: str) -> dict:
    """
    Quick heuristic checks before LLM scoring
    """
    from arabic_normalizer import normalize_arabic
    import re
    
    normalized = normalize_arabic(text)
    words = normalized.split()
    
    issues = []
    
    # 1. Keyword repetition
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Skip short words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    repeated_words = {w: c for w, c in word_freq.items() if c >= 5}
    if repeated_words:
        issues.append({
            "type": "keyword_repetition",
            "words": repeated_words,
            "severity": "medium"
        })
    
    # 2. All caps (screaming)
    if text.isupper():
        issues.append({
            "type": "all_caps",
            "severity": "high"
        })
    
    # 3. No punctuation
    if not any(p in text for p in [".", "!", "?", "،", "؟"]):
        issues.append({
            "type": "no_punctuation",
            "severity": "low"
        })
    
    # 4. English keywords in Arabic text
    english_pattern = re.compile(r'[a-zA-Z]{4,}')
    english_words = english_pattern.findall(text)
    if len(english_words) > 3:
        issues.append({
            "type": "mixed_language",
            "english_words": english_words,
            "severity": "medium"
        })
    
    # 5. SEO patterns (e.g., "احسن [keyword] في [location]" repeated)
    seo_patterns = [
        r'احسن .+ في .+',
        r'افضل .+ في .+',
        r'best .+ in .+'
    ]
    
    for pattern in seo_patterns:
        matches = re.findall(pattern, text)
        if len(matches) >= 3:
            issues.append({
                "type": "seo_template_repetition",
                "pattern": pattern,
                "severity": "high"
            })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "score": max(0, 10 - len(issues) * 2)  # Penalty-based score
    }
```

## AEO Readiness Indicators

Check for question-answering structure:

```python
def check_aeo_readiness(text: str, html_structure: str = None):
    """
    Check if content is structured for Answer Engines
    """
    from arabic_normalizer import normalize_arabic
    
    normalized = normalize_arabic(text)
    
    aeo_signals = []
    
    # 1. Direct Q&A headers
    question_patterns = [
        r'كيف استخدم',  # How to use
        r'ما هو',       # What is
        r'لماذا',       # Why
        r'متى',         # When
        r'اين',         # Where
    ]
    
    for pattern in question_patterns:
        if re.search(pattern, normalized):
            aeo_signals.append("direct_question")
    
    # 2. H2/H3 structure (if HTML provided)
    if html_structure:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_structure, 'html.parser')
        
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))
        
        if h2_count >= 2:
            aeo_signals.append("structured_headings")
    
    # 3. Experience signals (local dialect, specific scenarios)
    experience_patterns = [
        r'جربته',      # I tried it
        r'استخدمته',   # I used it
        r'ينفع ل',     # Good for (Khaliji)
        r'مناسب ل',    # Suitable for
    ]
    
    for pattern in experience_patterns:
        if re.search(pattern, normalized):
            aeo_signals.append("experience_signal")
    
    return {
        "aeo_ready": len(aeo_signals) >= 2,
        "signals": aeo_signals,
        "score": min(10, len(aeo_signals) * 3)
    }
```

## Combined Scoring

Aggregate all scoring methods:

```python
async def score_product_description(text: str, html: str = None):
    """
    Complete content quality scoring
    """
    
    # 1. Quick heuristic checks
    robotic_check = detect_robotic_patterns(text)
    
    # 2. AEO structure check
    aeo_check = check_aeo_readiness(text, html)
    
    # 3. LLM-based deep analysis (only if heuristics pass minimum threshold)
    if robotic_check["score"] >= 5:
        llm_score = await score_content_with_ollama(text)
    else:
        llm_score = {"naturalness": robotic_check["score"], "reasoning": "Failed heuristic checks"}
    
    # Combine scores
    final_score = {
        "overall": (robotic_check["score"] + aeo_check["score"] + llm_score.get("naturalness", 0)) / 3,
        "robotic_patterns": robotic_check,
        "aeo_readiness": aeo_check,
        "llm_analysis": llm_score,
        "recommendation": generate_recommendation(robotic_check, aeo_check, llm_score)
    }
    
    return final_score

def generate_recommendation(robotic, aeo, llm):
    """Generate actionable recommendations"""
    if robotic["score"] < 5:
        return "REWRITE: Content appears robotic or keyword-stuffed"
    elif aeo["score"] < 5:
        return "IMPROVE: Add Q&A structure and direct answers"
    elif llm.get("dialect_usage", 0) < 3:
        return "ENHANCE: Add regional dialect for authenticity"
    else:
        return "GOOD: Content is human-first and AEO-ready"
```

## Model Selection

**Recommended Ollama models for Arabic:**

1. **aya** (8B): Best multilingual Arabic support
2. **llama3** (8B): Good general reasoning, decent Arabic
3. **gemma2** (9B): Fast, lightweight

**Installation:**
```bash
ollama pull aya
ollama serve
```

## Output Format

```python
{
    "overall_score": 7.5,
    "robotic_patterns": {
        "score": 8,
        "issues": [...]
    },
    "aeo_readiness": {
        "score": 7,
        "signals": ["direct_question", "experience_signal"]
    },
    "llm_analysis": {
        "naturalness": 8,
        "keyword_stuffing_reverse": 7,
        "reasoning": "..."
    },
    "recommendation": "ENHANCE: Add regional dialect for authenticity"
}
```

## Critical Rules

- Always run heuristic checks first to save LLM calls
- Use local Ollama (privacy + speed) instead of cloud APIs
- Normalize Arabic text before pattern matching
- Scores below 5 require content rewrite
- Dialect usage is a positive signal (authenticity)
